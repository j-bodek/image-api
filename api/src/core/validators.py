import os
from django.core.exceptions import ValidationError
from typing import Protocol


class FileProtocol(Protocol):
    name: str


def img_extension_validator(value: FileProtocol) -> None:
    """Validate if uploaded file is either jpg or png"""

    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".jpg", ".jpeg", ".png"]
    if not ext.lower() in valid_extensions:
        raise ValidationError(
            f"'{ext.lower()}' is unnsupported image extension. "
            f"Supported extensions are: {', '.join(valid_extensions)}"
        )
