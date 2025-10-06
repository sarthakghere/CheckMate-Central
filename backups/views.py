from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_api_key.permissions import HasAPIKey
from .serializers import BackupUploadSerializer
from colleges.models import College
from rest_framework_api_key.models import APIKey

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
