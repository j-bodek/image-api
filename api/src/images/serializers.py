from rest_framework import serializers
from core import models, validators
import uuid


class ThumbnailSerializer(serializers.ModelSerializer):
    """
    Class used as Thumbnail Serializer
    """

    class Meta:
        model = models.Thumbnail
        fields = ("height", "width")


class ImageCreateSerializer(serializers.ModelSerializer):
    """
    Class used as Image Serializer
    """

    uuid = serializers.UUIDField(default=lambda: uuid.uuid4())
    file = serializers.ImageField(
        source="og_file", validators=[validators.img_extension_validator], required=True
    )

    class Meta:
        model = models.Image
        fields = (
            "uuid",
            "name",
            "file",
            "uploaded_at",
            "thumbnails",
        )
        read_only_fields = (
            "uploaded_at",
            "thumbnails",
        )
