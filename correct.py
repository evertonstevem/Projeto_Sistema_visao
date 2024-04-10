from math import ceil, pi, sqrt
from typing import cast

import cv2 as cv
from cv2.typing import MatLike

from logger import Logger
from self_types import Errors


class Correct:
    @classmethod
    def run(
        cls,
        image_save_file: str,
        read_image: str,
        errors: Errors,
    ):
        """
        Corrects the image and saves it to the disk.

        Parameters
        ----------

        image_save_file : str
            The path to save the image to.
        read_image : str
            The path to the image to read.
        errors : Errors
            The errors data.
        piece_data : NewData
            The piece data.
        diffs : dict[Literal["x", "y"], int | None]
            The diffs data.
        """

        Logger.debug("Running correct command.")
        Logger.debug("Reading image.")
        image = cls.__io_image(read_image, None)
        image = cast(MatLike, image)

        if errors["areas"] is not None:
            for error in errors["areas"]:
                color: tuple[int, int, int] = (255, 0, 0)
                position = (
                    (error["correct_center_px"]["x"] + 2000),
                    (error["correct_center_px"]["y"] + 1200),
                )
                if error["kind"] == "unexpected":
                    radius = 25
                    cv.line(
                        image,
                        (position[0] - radius, position[1] - radius),
                        (position[0] + radius, position[1] + radius),
                        color,
                        5,
                    )
                    cv.line(
                        image,
                        (position[0] - radius, position[1] + radius),
                        (position[0] + radius, position[1] - radius),
                        color,
                        5,
                    )
                    continue

                if error["kind"] == "unexistent":
                    color = (0, 0, 255)
                elif error["kind"] == "both":
                    color = (0, 255, 255)
                elif error["kind"] == "center":
                    color = (0, 255, 0)

                radius = ceil(sqrt((float(error["correct_area_px"]) / pi)))
                cv.circle(image, position, radius, color, 5)
                cv.putText(
                    image,
                    f"{error['id']}",
                    (position[0] - 60, position[1] - radius - 30),
                    cv.FONT_HERSHEY_SIMPLEX,
                    1.5,
                    color,
                    2,
                )

        image = image[1200 : 1200 + 4900, 2000 : 2000 + 5200]
        Logger.debug("Writing image.")
        cls.__io_image(image_save_file, image)
        Logger.debug("Correct command finished.")

    @classmethod
    def __io_image(cls, image_name: str, image: MatLike | None) -> MatLike | None:
        """
        Reads or writes an image. If image is None, it reads the image, otherwise it
        writes the image.

        Parameters
        ----------
        image_name : str
            The path to the image.
        image : MatLike | None
            The image to write.

        """
        if not image_name.endswith(".png"):
            # ! ERROR CODE 4
            Logger.err_exit(f"{image_name} is not PNG.", code=4)
        try:
            if image is None:
                return cv.imread(image_name, cv.IMREAD_COLOR)
            else:
                cv.imwrite(image_name, image)
                return
        except Exception as err:
            Logger.debug(f"{err}")
            # ! ERROR CODE 6
            Logger.err_exit(f"OPENCV | Unable to read/write {image_name}.", code=6)
