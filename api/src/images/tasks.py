import celery
import logging
from typing import Union
from django.core.files.base import ContentFile
from images.resizer import ImageResizer
from src import CELERY_APP, REDIS


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
        **context,  # any additional kwargs will be treated as email context
    ) -> None:
        """This method should define body of the task executed by workers"""
        from images.serializers import ThumbnailSerializer

        try:
            image_resizer = ImageResizer(
                image_uuid=image_uuid, thumbnails_data=thumbnails_data
            )
            for filename, size, img_bytes in image_resizer.resize():
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
        finally:
            # make sure that cached image is deleted from redis
            REDIS.delete(image_uuid)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """This method is called when task fails"""

        logging.error(
            f"{task_id} failed: {exc}\n",
            f"Failed to create thumbnails for image with uuid '{kwargs.get('image_uuid')}'\n",  # noqa
        )


thumbnails_creator = CELERY_APP.register_task(ThumbnailsCreator())
