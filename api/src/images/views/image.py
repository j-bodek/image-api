from rest_framework import generics, permissions, status
from images.serializers import ImageCreateSerializer
from rest_framework.response import Response


class ImageUploadView(generics.CreateAPIView):
    """
    View used to handle uploading images
    """

    serializer_class = ImageCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer: ImageCreateSerializer) -> None:
        serializer.save(uploaded_by=self.request.user)
