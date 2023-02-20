from django.core.files.storage import FileSystemStorage
from django.conf import settings
from typing import Union
import os


class OverwriteStorage(FileSystemStorage):
    """Overwrite FileSystemStorage class to overwrite
    file with same path. This storage is used to save images thumbnails"""

    def get_available_name(self, name: str, max_length: Union[None, int] = None) -> str:
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """

        # If the filename already exists, remove it
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
