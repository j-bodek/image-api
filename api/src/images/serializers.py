from rest_framework import serializers
from django.contrib.auth import get_user_model
from core import models, validators
from images.tasks import thumbnails_creator
from src import REDIS
from typing import Iterator
import os


class ThumbnailSerializer(serializers.ModelSerializer):
    """
    Class used as Thumbnail Serializer
    """

    class Meta:
        model = models.Thumbnail
        fields = ("image", "height", "width", "file")
        extra_kwargs = {"image": {"write_only": True}}


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer used to serialize many images (with thumbnails)
    """

    thumbnails = ThumbnailSerializer(many=True, read_only=True)

    class Meta:
        model = models.Image
        fields = (
            "name",
            "uploaded_at",
            "og_file",
            "thumbnails",
        )
        read_only_fields = (
            "name",
            "uploaded_at",
            "og_file",
            "thumbnails",
        )


class ImageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used to create images (with thumbnails)
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
            "name",
            "uploaded_at",
            "file",
            "og_file",
            "thumbnails",
        )
        read_only_fields = (
            "uploaded_at",
            "og_file",
            "thumbnails",
        )

    def get_thumbnails(self, obj: models.Image) -> dict:
        """Return serialized thumbnails data"""

        if not obj:
            return []

        try:
            self.validated_data["thumbnails"]
        except (KeyError, AssertionError):
            # if data wasn't validated yet or thumbnails doens't exists
            return []

        for data in self.validated_data["thumbnails"]:
            # update file to return url
            data.update(
                {
                    "file": models.Thumbnail.generate_absolute_url(
                        self.context["request"], str(obj.uuid), data["file"]
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
            width = size["width"] or "auto"
            height = size["height"] or "auto"

            yield {
                "width": size["width"],
                "height": size["height"],
                "file": f"thumbnail-{width}x{height}{extension}",
            }

    def create(self, validated_data: dict) -> models.Image:
        """
        Extended default ModelSerializer create method
        """

        user = self.context["request"].user
        extension = os.path.splitext(validated_data["og_file"].name)[1]

        file = validated_data["og_file"]
        # if user doesn't have permission to access original image
        # delete it from validated_data in order to prevent saving it
        if user.tier is None or not user.tier.has_og_image_access:
            del validated_data["og_file"]

        instance = super().create(validated_data)

        thumbnails_data = list(self.get_thumbnails_data(user, extension))

        if thumbnails_data:
            # cache image in redis for faster access in celery task
            REDIS.set(str(instance.uuid), file.file.getvalue())

            # run celery task
            thumbnails_creator.delay(
                image_uuid=str(instance.uuid), thumbnails_data=thumbnails_data
            )

        # set thumbnails in validated_data
        self._validated_data["thumbnails"] = thumbnails_data

        return instance
