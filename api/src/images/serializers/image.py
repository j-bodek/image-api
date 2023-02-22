from .thumbnail import ThumbnailSerializer
from rest_framework import serializers, exceptions
from django.contrib.auth import get_user_model
from core import models, validators
from images.tasks.registry import thumbnails_creator
from images.tokens import expiring_image_token_generator
from src import REDIS
from typing import Iterator, Union
from django.urls import reverse
import os


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer used to serialize many images (with thumbnails)
    """

    thumbnails = ThumbnailSerializer(many=True, read_only=True)
    can_fetch_expiring_image = serializers.BooleanField(
        source="uploaded_by.tier.can_generate_expire_link"
    )

    class Meta:
        model = models.Image
        fields = (
            "name",
            "uuid",
            "uploaded_at",
            "can_fetch_expiring_image",
            "og_file",
            "thumbnails",
        )
        read_only_fields = (
            "name",
            "uploaded_at",
            "can_fetch_expiring_image",
            "og_file",
            "thumbnails",
        )


class ExpiringImageSerializer(serializers.Serializer):
    """
    Serializer used to create an expiring image link
    """

    expiring_image_token_generator = expiring_image_token_generator

    # fields
    uuid = serializers.UUIDField(required=True, write_only=True)
    expire_time = serializers.IntegerField(required=True)
    url = serializers.URLField(required=False, read_only=True)

    class Meta:
        fields = (
            "uuid",
            "expire_time",
            "url",
        )
        read_only_fields = ("url",)

    def validate_expire_time(self, value: int) -> Union[int, None]:
        """Check if expire time is in range 300 - 30000"""

        if not (300 <= value <= 30000):
            raise serializers.ValidationError(
                "'expire_time' must be in range 300, 30000"
            )

        return value

    def generate_expire_img_url(self, token: str, filename: str) -> str:
        """Method used to generate expire image url. Returns absolute
        url if request in context otherwise returns relative path"""

        url = reverse(
            "images:image_expiring", kwargs={"token": token, "path": filename}
        )

        if "request" in self.context:
            return self.context["request"].build_absolute_uri(url)

        return url

    def create_expiring_img_link(self, image: models.Image) -> None:
        """Generate expiring img link"""

        if not image.og_file:
            raise exceptions.NotFound(
                "File for image with specified uuid does not exist. "
                "Make sure that 'og_file' for image with specified 'uuid' exists"
            )

        filename = image.og_file.name
        token = self.expiring_image_token_generator.make_token(
            filename, self.validated_data["expire_time"]
        )

        url = self.generate_expire_img_url(token=token, filename=filename)
        self._validated_data.update({"url": url})


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
    can_fetch_expiring_image = serializers.BooleanField(
        source="uploaded_by.tier.can_generate_expire_link"
    )
    thumbnails = serializers.SerializerMethodField()

    class Meta:
        model = models.Image
        fields = (
            "name",
            "uuid",
            "uploaded_at",
            "file",
            "can_fetch_expiring_image",
            "og_file",
            "thumbnails",
        )
        read_only_fields = (
            "uploaded_at",
            "can_fetch_expiring_image",
            "og_file",
            "thumbnails",
        )

    def get_thumbnails(self, obj: Union[models.Image, None]) -> Iterator:
        """Return serialized thumbnails data"""

        if not obj:
            return []

        try:
            self.validated_data["thumbnails"]
        except (KeyError, AssertionError):
            # if data wasn't validated yet or thumbnails doesn't exists
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
