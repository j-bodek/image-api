from django.test import SimpleTestCase
from core.validators import img_extension_validator
from django.core.exceptions import ValidationError
from unittest.mock import MagicMock


class TestImageExtensionValidator(SimpleTestCase):
    """Test if image extension validator raise ValidationError
    if file extension is not .jpg, .jpeg or .png"""

    def setUp(self):
        self.valid_extensions = [".jpg", ".jpeg", ".png"]
        self.invalid_extensions = [".gif", ".svg", ".pdf"]

    def test_valid_extensions(self):
        """Test if ValidationError is not raised"""

        for ext in self.valid_extensions:
            file = MagicMock()
            file.name = f"filename{ext}"
            img_extension_validator(file)

    def test_invalid_extensions(self):
        """Test if ValidationError is not raised"""

        for ext in self.invalid_extensions:
            with self.assertRaises(ValidationError):
                file = MagicMock()
                file.name = f"filename{ext}"
                img_extension_validator(file)
