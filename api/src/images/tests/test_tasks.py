from django.test import SimpleTestCase
from images.tasks.thumbnails_creator_task import ThumbnailsCreator
from unittest import mock
import uuid


class TestThumbnailsCreatorTask(SimpleTestCase):
    """Test ThumbnailsCreator celery task"""

    def setUp(self):
        self.task = ThumbnailsCreator()
        self.image_uuid = str(uuid.uuid4())
        self.thumbnails_data = [{"height": 200, "width": None, "file": "somefile.jpg"}]

    @mock.patch("images.tasks.thumbnails_creator_task.ImageResizer")
    @mock.patch("images.tasks.thumbnails_creator_task.ThumbnailsCreator.save_image")
    @mock.patch("images.tasks.thumbnails_creator_task.REDIS")
    def test_run(self, mocked_redis, mocked_save_image, mocked_resizer):
        """Test if ImageResizer.resize is called, and save_image is called
        with data returned by ImageResizer.resize"""

        resize_output = ("somefile.jpg", {"height": 200, "width": 300}, bytes())
        mocked_resizer_instance = mock.MagicMock()
        mocked_resizer_instance.resize.return_value = [resize_output]
        mocked_resizer.return_value = mocked_resizer_instance

        self.task.run(image_uuid=self.image_uuid, thumbnails_data=self.thumbnails_data)

        self.assertEqual(mocked_resizer_instance.resize.call_count, 1)
        mocked_save_image.assert_called_once_with(self.image_uuid, *resize_output)
        mocked_redis.delete.assert_called_once_with(self.image_uuid)

    @mock.patch("images.tasks.thumbnails_creator_task.ImageResizer")
    @mock.patch("images.tasks.thumbnails_creator_task.REDIS")
    def test_redis_delete_called_if_error_occure(self, mocked_redis, mocked_resizer):
        """Test if redis.delete is called if error occurs in run method"""

        mocked_resizer.side_effect = [AssertionError]
        self.task.run(image_uuid=self.image_uuid, thumbnails_data=self.thumbnails_data)
        mocked_redis.delete.assert_called_once_with(self.image_uuid)

    @mock.patch("images.tasks.thumbnails_creator_task.ThumbnailSerializer")
    def test_save_image(self, mocked_thumbanil_serialzier):
        """Test if ThumbnailSerializer is validated and then saved"""
        mocked_thumbanil_serialzier_instance = mock.MagicMock()
        mocked_thumbanil_serialzier.return_value = mocked_thumbanil_serialzier_instance

        data = {
            "image_uuid": self.image_uuid,
            "filename": "somefile.jpg",
            "size": {"height": 200, "width": 200},
            "img_bytes": bytes(),
        }

        self.task.save_image(**data)
        self.assertEqual(mocked_thumbanil_serialzier_instance.is_valid.call_count, 1)
        self.assertEqual(mocked_thumbanil_serialzier_instance.save.call_count, 1)
