from django.test import SimpleTestCase
from unittest import mock
from core.storage import OverwriteStorage
from django.conf import settings
import os


class TestOverwriteStorage(SimpleTestCase):
    """Test if OverwriteStorage in get_available_name remove existing
    file with provided name"""

    def setUp(self):
        self.filename = "image.jpg"
        self.storage = OverwriteStorage()

    @mock.patch("core.storage.OverwriteStorage.exists", return_value=True)
    @mock.patch("core.storage.os.remove")
    def test_existing_file(self, mocked_os_remove, *mocks):
        """Test if os.remove called"""

        filename = self.storage.get_available_name(self.filename)
        mocked_os_remove.assert_called_once_with(
            os.path.join(settings.MEDIA_ROOT, self.filename)
        )
        self.assertEqual(filename, self.filename)

    @mock.patch("core.storage.os")
    @mock.patch("core.storage.OverwriteStorage.exists", return_value=False)
    def test_not_existing_file(self, mocked_os, *mocks):
        """Test if os.remove called"""

        filename = self.storage.get_available_name(self.filename)
        self.assertEqual(mocked_os.remove.call_count, 0)
        self.assertEqual(filename, self.filename)
