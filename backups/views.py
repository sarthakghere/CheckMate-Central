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


def get_college_from_request(request):
    # Extract the key string from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Api-Key "):
        return None
    key_value = auth_header.split(" ")[1]

    # Convert to APIKey instance
    try:
        api_key = APIKey.objects.get_from_key(key_value)
        return College.objects.filter(api_key=api_key).first()
    except APIKey.DoesNotExist:
        return None

class BackupUploadAPIView(APIView):
    """
    Receives a MySQL backup file from an authenticated college.
    Requires header: Authorization: Api-Key <college_api_key>
    """
    permission_classes = [HasAPIKey]

    def post(self, request):
        college = get_college_from_request(request)
        if not college:
            return Response({"error": "Invalid API key"}, status=403)
        
        serializer = BackupUploadSerializer(data=request.data)
        if serializer.is_valid():
            backup = serializer.save(college=college)
            return Response({
                "message": "Backup uploaded successfully.",
                "college": college.code,
                "file_size": backup.file_size,
                "checksum": backup.checksum,
                "uploaded_at": backup.uploaded_at,
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@login_required
def backup_list(request):
    if request.user.role != "STAFF":
        return HttpResponse("Unauthorized", status=403)

    colleges = College.objects.all()
    # Precompute last backup for better template logic
    college_last_backups = {
        college.id: college.backups.order_by('-uploaded_at').first() for college in colleges
    }
    context = {"colleges": colleges, "college_last_backups": college_last_backups}
    return render(request, "backups/backup_list.html", context)


@login_required
def college_backup_list(request, college_id):
    # if request.user.role != "STAFF":
    #     return HttpResponse("Unauthorized", status=403)

    college = get_object_or_404(College, id=college_id)
    backups = Backup.objects.filter(college=college).order_by('-uploaded_at')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        backups = backups.filter(uploaded_at__date__gte=start_date)
    if end_date:
        backups = backups.filter(uploaded_at__date__lte=end_date)

    if 'download' in request.GET:
        if not backups.exists():
            return HttpResponse("No backups found for the selected criteria.", status=404)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for backup in backups:
                if os.path.exists(backup.file.path):
                    # Create a relative path for the file in the zip archive
                    relative_path = os.path.join(college.code, os.path.basename(backup.file.name))
                    zip_file.write(backup.file.path, relative_path)

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type="application/zip")
        
        filename = f'backups_{college.code}'
        if start_date:
            filename += f'_{start_date}'
        if end_date:
            filename += f'_{end_date}'
        filename += '.zip'

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    context = {
        "college": college, 
        "backups": backups,
        "start_date": start_date,
        "end_date": end_date,
        "total_size": sum(b.file.size for b in backups if b.file and os.path.exists(b.file.path))
    }
    return render(request, "backups/college_backup_list.html", context)


@login_required
def download_backup(request, backup_id):

    backup = get_object_or_404(Backup, id=backup_id)
    file_path = backup.file.path

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
    raise Http404
