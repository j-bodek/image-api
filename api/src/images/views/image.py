from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from images.serializers import ImageCreateSerializer, ExpiringImageSerializer
from images.permissions import IsImageOwner, IsExpiringImageTokenValid
from core.models import Image
from typing import Union
from django.conf import settings
from django.views.static import serve


class ImageUploadView(generics.CreateAPIView):
    """
    View used to handle uploading images.
    It takes following post parameters:
    - name - name of the image
    - file - image in format jpg or png
    """

    serializer_class = ImageCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer: ImageCreateSerializer) -> None:
        serializer.save(uploaded_by=self.request.user)


class GenerateExpiringImageView(generics.CreateAPIView):
    """
    View used to generate expiring image link.
    It takes following post parameters:
    - uuid - uuid of image
    - expire_time - link expiration time (in seconds)
    """

    serializer_class = ExpiringImageSerializer
    permission_classes = (permissions.IsAuthenticated, IsImageOwner)

    def get_object(self) -> Union[None, Image]:
        """Get Image object based on 'uuid' parameter or return None if uuid
        is not provided"""

        if "uuid" not in self.request.data:
            return

        try:
            obj = generics.get_object_or_404(Image, uuid=self.request.data["uuid"])
        except:
            raise exceptions.NotFound("Image with specified uuid does not exist")

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def create(self, request, *args, **kwargs):
        # validate incoming data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # generate expiring link image
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer: ExpiringImageSerializer) -> None:
        """Generate expiring link image"""

        # this will check object permissions
        image = self.get_object()
        serializer.create_expiring_img_link(image=image)


class ExpiringImageView(generics.RetrieveAPIView):
    """
    View used to handle expiring image endpoint. If token isn't expired
    it returns image
    """

    authentication_classes = ()
    permission_classes = (permissions.AllowAny, IsExpiringImageTokenValid)

    def retrieve(self, request, token, path, *args, **kwargs):
        """Serve image using FileResponse"""

        return serve(request, path=path, document_root=settings.MEDIA_ROOT)
