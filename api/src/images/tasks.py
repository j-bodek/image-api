import celery
import logging
from typing import Union
from django.core.files.base import ContentFile
from src import CELERY_APP, REDIS
from PIL import Image as PILImage
import io
import os


class ThumbnailsCreator(celery.Task):
    """
    This Task is used to create thumbnails of image
    uploaded by user.
    """

    def run(
        self,
        image_uuid: str,  # uuid to image model instance and to redis image data
        # in format [{"height":height, "width":width, "file":filename}]
        thumbnails_data: list[dict[str, Union[str, int, None]]],
        **context,  # any additional kwargs will be treated as email context
    ) -> None:
        """This method should define body of the task executed by workers"""
        from images.serializers import ThumbnailSerializer

        try:
            for thumbnail in thumbnails_data:
                ext = os.path.splitext(thumbnail["file"])[1]
                new_height, new_width = thumbnail["height"], thumbnail["width"]
                img_bytes = self.__resize_image(image_uuid, ext, new_height, new_width)
                image = ContentFile(img_bytes, name=thumbnail["file"])
                serializer = ThumbnailSerializer(
                    data={
                        "image": image_uuid,
                        "height": new_height,
                        "width": new_width,
                        "file": image,
                    }
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
        finally:
            # make sure that cached image is deleted from redis
            REDIS.delete(image_uuid)

    def __resize_image(
        self,
        image_uuid: str,
        extension: str,
        height: Union[str, None],
        width: Union[str, None],
    ) -> bytes:
        """Return resized version of image cached in redis and returns it as bytes"""

        image = REDIS.get(image_uuid)
        image = PILImage.open(io.BytesIO(image))
        if None not in [height, width]:
            image.resize((width, height), PILImage.ANTIALIAS)
        elif [height, width].count(None) == 1:
            scale_ratio = self.__get_resize_ratio(image.size, height, width)
            image = image.resize(
                (int(s * scale_ratio) for s in image.size), PILImage.ANTIALIAS
            )
        else:
            # image remain as it was
            pass

        output = io.BytesIO()
        image.save(
            output, format=self.__get_format(extension), optimize=True, quality=80
        )

        return output.getvalue()

    def __get_format(self, extension: str) -> str:
        """Used to get format used to save resized image to bytesIO"""

        return {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
        }.get(extension.lower())

    def __get_resize_ratio(
        self,
        basesize: tuple[int],  # (width, height)
        newheight: Union[int, None],
        newwidth: Union[int, None],
    ) -> float:
        """Returns resize ration, used when scaling image based only or height or width"""
        height_ratio = None if newheight is None else newheight / basesize[1]
        width_ratio = None if newwidth is None else newwidth / basesize[0]

        return height_ratio or width_ratio

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """This method is called when task fails"""

        logging.error(
            f"{task_id} failed: {exc}\n",
            f"Failed to create thumbnails for image with uuid '{kwargs.get('image_uuid')}'\n",  # noqa
        )


thumbnails_creator = CELERY_APP.register_task(ThumbnailsCreator())
