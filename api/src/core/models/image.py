from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import os


class AbstractImage(models.Model):
    """Define base abstract Image Model"""

    folder_name = "images"

    class Meta:
        abstract = True

    def get_upload_to(self, filename: str) -> str:
        """get path where images should be uploaded"""

        filename = self.og_file.field.storage.get_valid_name(filename)
        return os.path.join(self.folder_name, filename)


def get_upload_to(instance: AbstractImage, filename: str) -> str:
    """Return path to location where file should be uploaded"""

    return instance.get_upload_to(filename)


class Image(AbstractImage):
    """
    Model used to store uploaded images
    and their data
    """

    # this field will be used to identify images
    uuid = models.UUIDField(
        null=False,
        blank=False,
        editable=False,
        unique=True,
    )
    name = models.CharField(
        null=False,
        blank=False,
        max_length=255,
    )
    og_file = models.ImageField(
        null=True,
        blank=True,
        uploaded_to=get_upload_to,
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


class Thumbnail(AbstractImage):
    """
    This model is used to store resized
    images and their data
    """

    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    file = models.ImageField(
        null=False,
        blank=False,
        uploaded_to=get_upload_to,
    )
