from rest_framework import serializers
from core import models
import uuid


class ThumbnailSerializer(serializers.ModelSerializer):
    """
    Class used as Thumbnail Serializer
    """

    class Meta:
        model = models.Thumbnail
        fields = ("height", "width")


class ImageSerializer(serializers.ModelSerializer):
    """
    Class used as Image Serializer
    """

    uuid = serializers.UUIDField(default=lambda: uuid.uuid4())
    thumbnails = ThumbnailSerializer(source="image.thumbnails", read_only=True)

    class Meta:
        model = models.Image
        fields = (
            "uuid",
            "name",
            "og_file",
            "uploaded_at",
            "thumbnails",
        )
        read_only_fields = (
            "uploaded_at",
            "thumbnails",
        )
