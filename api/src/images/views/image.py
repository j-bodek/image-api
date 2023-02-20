from rest_framework import generics, permissions
from images.serializers import ImageCreateSerializer


class ImageUploadView(generics.CreateAPIView):
    """
    View used to handle uploading images
    """

    serializer_class = ImageCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer: ImageCreateSerializer) -> None:
        serializer.save(uploaded_by=self.request.user)
