from rest_framework import generics, permissions, status
from images.serializers import ImageSerializer
from rest_framework.response import Response


class ImageUploadView(generics.CreateAPIView):
    """
    View used to handle uploading images
    """

    serializer_class = ImageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer: ImageSerializer) -> None:
        serializer.save(uploaded_by=self.request.user)
