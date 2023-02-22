from dataclasses import dataclass
from typing import Union, Iterator
from src import REDIS
from PIL import Image as PILImage
import concurrent.futures
import io
import os


@dataclass
class ImageResizer:
    """
    This class is used to resize list of images.
    It takes list of dictionaries in following format.
    [{
        "file"[str]: filename # image name with extension (e.g. 'image.png')
        "height"[int]: new_height, # image height after resize
        "width"[int]: new_width, # image width after resize
    },]
    And image_uuid - key to image cached in redis that will be resized
    """

    image_uuid: str
    thumbnails_data: list[dict[str : Union[str, tuple]]]  # noqa

    def resize(self) -> Iterator[tuple[dict[str:int], str, bytes]]:
        """
        Generate resized images and yield tuples in following format:
        filename, {"height":new_height, "width":new_width}, img_bytes
        """

        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = []
            for thumbnail in self.thumbnails_data:
                results.append(
                    executor.submit(
                        self.resize_image, image_uuid=self.image_uuid, **thumbnail
                    )
                )

            # wait for functions to complete and yield their results
            for f in concurrent.futures.as_completed(results):
                yield f.result()

    def resize_image(
        self,
        image_uuid: str,
        file: str,  # image name with extension (e.g. 'image.png')
        height: Union[str, None],
        width: Union[str, None],
    ) -> tuple[dict[str:int], bytes]:
        """
        Return resized version of image cached in redis and returns it as bytes
        ,it new sizes and filename
        """

        image = REDIS.get(image_uuid)
        image = PILImage.open(io.BytesIO(image))

        if None not in [height, width]:
            image = image.resize((width, height), PILImage.ANTIALIAS)
        elif [height, width].count(None) == 1:
            scale_ratio = self.__get_resize_ratio(image.size, height, width)
            image = image.resize(
                (int(s * scale_ratio) for s in image.size), PILImage.ANTIALIAS
            )
        else:
            # image remain as it was
            pass

        output = io.BytesIO()
        extension = os.path.splitext(file)[1]
        image.save(
            output, format=self.__get_format(extension), optimize=True, quality=80
        )
        new_size = {"width": image.size[0], "height": image.size[1]}

        return file, new_size, output.getvalue()

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
        """
        Returns resize ration, used when scaling image based only or height or width
        """

        height_ratio = None if newheight is None else newheight / basesize[1]
        width_ratio = None if newwidth is None else newwidth / basesize[0]

        return height_ratio or width_ratio
