from django.db import models
from django.conf import settings
from django.http import HttpRequest
from core.storage import OverwriteStorage
from core import validators
from typing import Protocol
import uuid
import os


class ImageModelProtocol(Protocol):
    """Define Image Model interface"""

    def get_upload_to(self, filename: str) -> str:
        ...


def get_upload_to(instance: ImageModelProtocol, filename: str) -> str:
    """Return path to location where file should be uploaded"""

    return instance.get_upload_to(filename)


class Image(models.Model):
    """
    Model used to store uploaded images
    and their data
    """

    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        max_length=36,
    )

    name = models.CharField(
        null=False,
        blank=False,
        max_length=255,
    )
    og_file = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_upload_to,
        validators=[validators.img_extension_validator],
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        editable=False,
        on_delete=models.CASCADE,
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    # class attributes
    folder_name = "original_images"

    def get_upload_to(self, filename: str) -> str:
        """get path where images should be uploaded"""

        filename = self.og_file.field.storage.get_valid_name(filename)
        return os.path.join(self.folder_name, filename)


class Thumbnail(models.Model):
    """
    This model is used to store resized
    images and their data
    """

    image = models.ForeignKey(
        Image,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name="thumbnails",
    )
    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    file = models.ImageField(
        null=False,
        blank=False,
        # this will make sure that images with same name will be overwritten,
        # doing that we can be sure that file will be saved with provided filename
        storage=OverwriteStorage(),
        upload_to=get_upload_to,
        validators=[validators.img_extension_validator],
    )

    # class attributes
    folder_name = "thumbnails"

    @classmethod
    def generate_absolute_url(
        cls, request: HttpRequest, image_uuid: str, filename: str
    ) -> str:
        """Generates thumbnail absolute URL"""

        path = cls.generate_upload_to(image_uuid, filename)
        url = cls.file.field.storage.url(path)
        return request.build_absolute_uri(url)

    @classmethod
    def generate_upload_to(cls, image_uuid: str, filename: str) -> str:
        """Provide method that generates path of thumbnail and can be used on class"""

        return os.path.join(cls.folder_name, image_uuid, filename)

    def get_upload_to(self, filename: str) -> str:
        """get path where thumbnail should be uploaded"""

        return self.generate_upload_to(str(self.image.uuid), filename)
