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
        source="og_file",
        write_only=True,
        validators=[validators.img_extension_validator],
        required=True,
    )

    class Meta:
        model = models.Image
        fields = (
            "uuid",
            "name",
            "uploaded_at",
            "file",
            "og_file",
        )
        read_only_fields = (
            "uploaded_at",
            "og_file",
        )

    def create(self, validated_data: dict) -> models.Image:
        """
        Extended default ModelSerializer create method
        """

        user = self.context["request"].user
        if user.tier is None or not user.tier.has_og_image_access:
            del validated_data["og_file"]

        return super().create(validated_data)
