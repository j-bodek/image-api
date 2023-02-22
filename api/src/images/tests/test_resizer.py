from django.test import SimpleTestCase
from images.resizer import ImageResizer
from unittest import mock
from pathlib import Path
from PIL import Image as PILImage
import io
import os


class TestImageResizer(SimpleTestCase):
    """Class to test image resizer class"""

    def setUp(self):
        self.resizer = ImageResizer

    def get_file_path(self, filename):
        """Return path to images folder"""

        TEST_DIR = Path(__file__).resolve().parent
        return os.path.join(TEST_DIR, f"images/{filename}")

    def read_image_from_file(self, path: str) -> bytes:
        """Helper function used to read image from file. It
        will be used to mock geting image bytes from redis"""

        with open(path, "rb") as f:
            return f.read()

    def get_thumbnails_data(self, extension: str) -> tuple[list, dict]:
        """Returns list of thumbnails data and expected sizes of scaled images"""

        thumbnails_data = [
            {"file": f"file1{extension}", "height": 200, "width": 200},
            {"file": f"file2{extension}", "height": 300, "width": None},
            {"file": f"file3{extension}", "height": None, "width": 400},
            {"file": f"file4{extension}", "height": None, "width": None},
        ]

        expected_sizes = {
            f"file1{extension}": (200, 200),
            f"file2{extension}": (300, 300),
            f"file3{extension}": (400, 400),
            f"file4{extension}": (800, 800),
        }

        return thumbnails_data, expected_sizes

    def check_resize(self, extension: str):
        """Helper function used to check if files was resized correctly
        for given format"""

        thumbnails_data, expected_sizes = self.get_thumbnails_data(extension=".jpg")
        resizer = self.resizer(image_uuid="uuid", thumbnails_data=thumbnails_data)

        for file, new_size, img_bytes in resizer.resize():
            scaled_image = PILImage.open(io.BytesIO(img_bytes))
            self.assertEqual(scaled_image.size[0], new_size["width"])
            self.assertEqual(scaled_image.size[1], new_size["height"])
            self.assertEqual(scaled_image.size, expected_sizes[file])

    @mock.patch("images.resizer.REDIS")
    def test_resize_method_with_jpg(self, mocked_redis):
        """Test resize_image method with jpg file"""

        mocked_redis.get.return_value = self.read_image_from_file(
            path=self.get_file_path("puffin.jpg")
        )
        self.check_resize(extension=".jpg")

    @mock.patch("images.resizer.REDIS")
    def test_resize_method_with_jpeg(self, mocked_redis):
        """Test resize_image method with jpeg file"""

        mocked_redis.get.return_value = self.read_image_from_file(
            path=self.get_file_path("puffin.jpeg")
        )
        self.check_resize(extension=".jpeg")

    @mock.patch("images.resizer.REDIS")
    def test_resize_method_with_png(self, mocked_redis):
        """Test resize_image method with png file"""

        mocked_redis.get.return_value = self.read_image_from_file(
            path=self.get_file_path("puffin.png")
        )
        self.check_resize(extension=".png")
