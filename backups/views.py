from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_api_key.permissions import HasAPIKey
from .serializers import BackupUploadSerializer
from colleges.models import College
from rest_framework_api_key.models import APIKey
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.conf import settings
import os
from .models import Backup
from io import BytesIO
import zipfile
import logging
from tempfile import NamedTemporaryFile
from .utils.encryption import decrypt_file

logger = logging.getLogger(__name__)


def get_user_info(request):
    """Return formatted user info string for logging."""
    if hasattr(request, "user") and request.user.is_authenticated:
        return f"{request.user.email} (Role: {getattr(request.user, 'role', 'UNKNOWN')})"
    return "Anonymous or API user"


def get_college_from_request(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Api-Key "):
        logger.warning("Invalid or missing Authorization header in backup upload request.")
        return None

    key_value = auth_header.split(" ")[1]

    try:
        api_key = APIKey.objects.get_from_key(key_value)
        college = College.objects.filter(api_key=api_key).first()
        if not college:
            logger.warning("API key is valid but no associated college found.")
        return college
    except APIKey.DoesNotExist:
        logger.warning(f"Backup upload attempted with invalid API key: {key_value}")
        return None


class BackupUploadAPIView(APIView):
    """
    Receives a MySQL backup file from an authenticated college.
    Requires header: Authorization: Api-Key <college_api_key>
    """
    permission_classes = [HasAPIKey]

    def post(self, request):
        college = get_college_from_request(request)
        user_info = get_user_info(request)

        if not college:
            logger.warning(f"{user_info} attempted unauthorized backup upload (invalid API key).")
            return Response({"error": "Invalid API key"}, status=403)

        serializer = BackupUploadSerializer(data=request.data)
        if serializer.is_valid():
            backup = serializer.save(college=college)
            logger.info(
                f"Backup uploaded successfully for {college.name} ({college.code}) "
                f"by {user_info}. Size: {backup.file_size} bytes"
            )
            return Response({
                "message": "Backup uploaded successfully.",
                "college": college.code,
                "file_size": backup.file_size,
                "checksum": backup.checksum,
                "uploaded_at": backup.uploaded_at,
            }, status=status.HTTP_201_CREATED)

        logger.error(
            f"Backup upload failed validation for {college.name} ({college.code}) by {user_info}. "
            f"Errors: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
def backup_list(request):
    user_info = get_user_info(request)

    if request.user.role != "STAFF":
        logger.warning(f"Unauthorized access to backup list by {user_info}")
        return HttpResponse("Unauthorized", status=403)

    colleges = College.objects.all()
    college_last_backups = {
        college.id: college.backups.order_by('-uploaded_at').first() for college in colleges
    }

    logger.info(f"Backup list viewed by {user_info}")
    context = {"colleges": colleges, "college_last_backups": college_last_backups}
    return render(request, "backups/backup_list.html", context)


@login_required
def college_backup_list(request, college_id):
    user_info = get_user_info(request)

    college = get_object_or_404(College, id=college_id)
    backups = Backup.objects.filter(college=college).order_by('-uploaded_at')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date or end_date:
        logger.info(
            f"Backup filter applied by {user_info} for {college.code}: "
            f"start_date={start_date}, end_date={end_date}"
        )

    if start_date:
        backups = backups.filter(uploaded_at__date__gte=start_date)
    if end_date:
        backups = backups.filter(uploaded_at__date__lte=end_date)

    if 'download' in request.GET:
        if not backups.exists():
            logger.warning(
                f"No backups found for {college.code} "
                f"({start_date} → {end_date}) requested by {user_info}"
            )
            return HttpResponse("No backups found for the selected criteria.", status=404)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for backup in backups:
                if os.path.exists(backup.file.path):
                    if backup.is_encrypted:
                        with NamedTemporaryFile(delete=False) as temp_file:
                            decrypt_file(backup.file.path, temp_file.name)
                            temp_file.seek(0)
                            relative_path = os.path.join(college.code, os.path.basename(backup.file.name).replace(".enc", ""))
                            zip_file.write(temp_file.name, relative_path)
                    else:
                        relative_path = os.path.join(college.code, os.path.basename(backup.file.name))
                        zip_file.write(backup.file.path, relative_path)
                else:
                    logger.error(
                        f"Backup file not found on disk for {college.code}: {backup.file.path}"
                    )

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type="application/zip")

        filename = f'backups_{college.code}'
        if start_date:
            filename += f'_{start_date}'
        if end_date:
            filename += f'_{end_date}'
        filename += '.zip'

        logger.info(
            f"Backups downloaded for {college.code} by {user_info} "
            f"({backups.count()} files)"
        )

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    logger.info(f"Backup list viewed by {user_info} for college {college.code}")
    context = {
        "college": college,
        "backups": backups,
        "start_date": start_date,
        "end_date": end_date,
        "total_size": sum(
            b.file.size for b in backups if b.file and os.path.exists(b.file.path)
        ),
    }
    return render(request, "backups/college_backup_list.html", context)

@login_required
def download_backup(request, backup_id):
    user_info = get_user_info(request)
    backup = get_object_or_404(Backup, id=backup_id)
    file_path = backup.file.path

    if not os.path.exists(file_path):
        logger.error(f"Missing backup for {user_info}: {file_path}")
        raise Http404

    logger.info(f"Backup downloaded by {user_info} ({backup.college.code}) - {file_path}")

    if backup.is_encrypted:
        with NamedTemporaryFile(delete=False) as temp_file:
            decrypt_file(file_path, temp_file.name)
            temp_file.seek(0)
            response = HttpResponse(temp_file.read(), content_type="application/octet-stream")
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path).replace(".enc", "")}"'
    else:
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'

    return response
