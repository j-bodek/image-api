from rest_framework import serializers
from core import models


class ThumbnailSerializer(serializers.ModelSerializer):
    """
    Class used as Thumbnail Serializer
    """

    class Meta:
        model = models.Thumbnail
        fields = ("image", "height", "width", "file")
        extra_kwargs = {"image": {"write_only": True}}
