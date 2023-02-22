from django.core.files.base import ContentFile
from images.resizer import ImageResizer
from images.serializers.thumbnail import ThumbnailSerializer
from src import REDIS
from typing import Union
import logging
import celery


class ThumbnailsCreator(celery.Task):
    """
    This Task is used to create thumbnails of image
    uploaded by user.
    """

    max_retries = 0

    def run(
        self,
        image_uuid: str,  # uuid to image model instance and to redis image data
        # in format [{"height":height, "width":width, "file":filename}]
        thumbnails_data: list[dict[str, Union[str, int, None]]],
        **kwargs,  # any additional kwargs
    ) -> None:
        """This method should define body of the task executed by workers"""

        try:
            image_resizer = ImageResizer(
                image_uuid=image_uuid, thumbnails_data=thumbnails_data
            )
            for filename, size, img_bytes in image_resizer.resize():
                self.save_image(image_uuid, filename, size, img_bytes)
        except Exception:
            logging.exception("message")
        finally:
            # make sure that cached image is deleted from redis
            REDIS.delete(image_uuid)

    def save_image(
        self, image_uuid: str, filename: str, size: dict[str:int], img_bytes: bytes
    ) -> None:
        """Create ContentFile and save Thumbnail"""

        image = ContentFile(img_bytes, name=filename)
        serializer = ThumbnailSerializer(
            data={
                "image": image_uuid,
                "height": size["height"],
                "width": size["width"],
                "file": image,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """This method is called when task fails"""

        logging.error(
            f"{task_id} failed: {exc}\n",
            f"Failed to create thumbnails for image with uuid '{kwargs.get('image_uuid')}'\n",  # noqa
        )
