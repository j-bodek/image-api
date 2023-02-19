import os
from django.core.exceptions import ValidationError


def img_extension_validator(value: str) -> None:
    """Validate if uploaded file is either jpg or png"""

    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".jpg", ".png"]
    if not ext.lower() in valid_extensions:
        raise ValidationError(
            f"'{ext.lower()}' is unnsupported image extension. "
            f"Supported extensions are: {', '.join(valid_extensions)}"
        )
