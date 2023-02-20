from rest_framework import serializers
from django.contrib.auth import get_user_model
from core import models, validators
from typing import Iterator
import os


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

    file = serializers.ImageField(
        source="og_file",
        write_only=True,
        validators=[validators.img_extension_validator],
        required=True,
    )
    thumbnails = serializers.SerializerMethodField()

    class Meta:
        model = models.Image
        fields = (
            "uuid",
            "name",
            "uploaded_at",
            "uploaded_by",
            "file",
            "og_file",
            "thumbnails",
        )
        read_only_fields = (
            "uploaded_at",
            "uploaded_by",
            "og_file",
            "thumbnails",
        )

    def get_thumbnails(self, obj: models.Image) -> dict:
        """Return serialized thumbnails data"""

        try:
            self.validated_data["thumbnails"]
        except (KeyError, AssertionError):
            # if data wasn't validated yet or thumbnails doens't exists
            return []

        uuid = str(self.data["uuid"])
        for data in self.validated_data["thumbnails"]:
            # update file to return url
            data.update(
                {
                    "file": models.Thumbnail.generate_absolute_url(
                        self.context["request"], uuid, data["file"]
                    )
                }
            )
            yield data

    def get_thumbnails_data(
        self, user: get_user_model(), extension: str
    ) -> Iterator[dict]:
        """Return thumbnails data based on user tier. It will be then used
        to create thumbnails in celery task and to generate data returned in response"""

        # if user is not connected with any tier return empty list
        # to prevent creating any thumbnails
        if user.tier is None:
            return []

        # get thumbnail sizes (without repeats)
        thumbnail_sizes = user.tier.sizes.values("height", "width").distinct()
        for size in thumbnail_sizes:
            height = size["height"] or "auto"
            width = size["width"] or "auto"

            yield {
                "height": size["height"],
                "width": size["width"],
                "file": f"thumbnail-{height}x{width}{extension}",
            }

    def create(self, validated_data: dict) -> models.Image:
        """
        Extended default ModelSerializer create method
        """

        user = self.context["request"].user
        extension = os.path.splitext(validated_data["og_file"].name)[1]

        # if user doesn't have permission to access original image
        # delete it from validated_data in order to prevent saving it
        if user.tier is None or not user.tier.has_og_image_access:
            del validated_data["og_file"]

        instance = super().create(validated_data)

        thumbnails_data = self.get_thumbnails_data(user, extension)
        # # TODO cache image in redis
        # # TODO run celery task

        # set thumbnails in validated_data
        self._validated_data["thumbnails"] = thumbnails_data

        return instance
