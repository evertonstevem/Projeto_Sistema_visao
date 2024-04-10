from decimal import Decimal
from json import dump
from os import getenv, path
from typing import Tuple, cast

import cv2 as cv
import numpy as np
from cv2.typing import MatLike

from logger import Logger
from self_types import NewData
from utils import DecimalEncoder, pitagoras_distance


class Process:
    """
    The class responsible for processing an image and getting it's information into a
    json.
    """

    MM_PER_PIXEL = Decimal(getenv("MM_PER_PIXEL", "0.2036"))
    MM_PER_PIXEL_SQUARE = Decimal(getenv("MM_PER_PIXEL_SQUARE", "0.1979")) ** 2
    CANNY_THRESHOLD_LOW = 255
    CANNY_THRESHOLD_HIGH = 255

    @classmethod
    def run(cls, read_image: str, json_file: str):
        """Run the process command."""

        Logger.debug("Running process command.")
        Logger.debug(f"MM_PER_PIXEL: {cls.MM_PER_PIXEL}")

        if not read_image.endswith(".png"):
            # ! ERROR CODE 4
            Logger.err_exit(f"{read_image} is not PNG.", code=4)

        if not path.isfile(read_image):
            # ! ERROR CODE 5
            Logger.err_exit(f"{read_image} not found.", code=5)

        image = cv.imread(read_image, cv.IMREAD_GRAYSCALE)
        if image is None:
            # ! ERROR CODE 6
            Logger.err_exit(f"OPENCV | Unable to read/write {read_image}.", code=6)

        # * For debugging purposes
        _, image = cv.threshold(image, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
        cv.imwrite("./images/output/original.png", image)

        image = image[1200 : 1200 + 4900, 2000 : 2000 + 5200]
        cv.imwrite("./images/output/cropped.png", image)
        # ? Still got to decide if we're going to use Gaussian Blur or not
        # image = cv.GaussianBlur(image, (5, 5), 0)

        box, canny = cls.__get_min_area_rect(image)

        # * For debugging purposes
        cv.imwrite("./images/output/outputcanny.png", canny)
        cv.imwrite("./images/output/outputimage.png", image)

        contours = cls.__get_contours(canny, box)

        Logger.debug(f"Box points: {box[0]}, {box[1]}, {box[2]}, {box[3]}.")
        box = cls.__sort_box_points(box)
        Logger.debug(f"Sorted box points: {box[0]}, {box[1]}, {box[2]}, {box[3]}.")

        # * For debugging purposes
        cv.imwrite("./images/output/output1.png", image)

        result = cls.__get_areas(image, contours[2:], box)

        cls.__save_json(f"{json_file}.json", result)

        Logger.info("Process command finished.")

    @classmethod
    def __get_min_area_rect(cls, image: MatLike) -> Tuple[MatLike, MatLike]:
        """
        Get the minimum area rectangle of the biggest contour of an image and put it in
        the image.

        Returns
        -------

        MatLike
            The rectangle enclosing points.
        MatLike
            The canny edge detection of the image wihout the rectangle.
        """

        Logger.info("Getting minimum area rectangle.")

        # Get the edges of the image
        canny = cv.Canny(image, cls.CANNY_THRESHOLD_LOW, cls.CANNY_THRESHOLD_HIGH)
        kernel = np.ones((2, 2), np.uint8)
        canny = cv.morphologyEx(canny, cv.MORPH_GRADIENT, kernel)
        # Get the contours of the image
        contours, _ = cv.findContours(canny, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        # Sort contours
        contours = sorted(contours, key=cv.contourArea, reverse=True)

        if len(contours) <= 1:
            # ! ERROR CODE 7
            Logger.err_exit("No piece found.", code=7)

        # Get the minimum area rectangle
        rect = cv.minAreaRect(contours[0])

        # Get the points of the rectangle
        box = cv.boxPoints(rect)
        box = cast(np.ndarray, box)
        box = np.int_(box)
        box = cast(MatLike, box)

        # cv.drawContours(image, [box], 0, (0, 0, 0), 10)

        if len(box) != 4:
            # ! ERROR CODE 8
            Logger.err_exit("No min area rect found.", code=8)

        return box, canny

    @classmethod
    def __get_contours(cls, canny: MatLike, box: MatLike) -> list[MatLike]:
        """
        Get the contours of the image and return then sorted.

        Returns
        -------

        list[MatLike]
            The contours sorted in biggest to smallest.

        """

        Logger.info("Getting contours of image.")

        # canny = cv.drawContours(canny, [box], 0, (255, 255, 255), 23)
        # canny = cv.rectangle(
        #     canny,
        #     (box[0][0], box[0][1]),
        #     (box[2][0], box[2][1]),
        #     0,
        #     int(Decimal("1.6") // cls.MM_PER_PIXEL),
        # )
        contours, _ = cv.findContours(canny, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv.contourArea, reverse=True)

        # * For debugging purposes
        cv.imwrite("./images/output/output2.png", canny)

        return contours

    @classmethod
    def __sort_box_points(cls, box: MatLike) -> list[list[int]]:
        """
        Sort the box points so the points are in a clockwise order coming from the
        top-left.


        Returns
        -------

        list[MatLike]
            The sorted box points clockwise from top-left
        """

        Logger.info("Sorting box points clockwise.")

        sort_x = box[box[:, 0].argsort()]
        sort_y = box[box[:, 1].argsort()]
        x_list: list[list[int]] = sort_x.tolist()

        if sort_x[1][0] == sort_y[0][0]:
            if abs(sort_x[0][1] - sort_x[1][1]) <= abs(sort_x[1][0] - sort_x[3][0]):
                return [x_list[1], x_list[3], x_list[2], x_list[0]]
            else:
                return [x_list[0], x_list[1], x_list[3], x_list[2]]
        else:
            if abs(sort_x[0][1] - sort_x[1][1]) <= abs(sort_x[0][0] - sort_x[2][0]):
                return [x_list[0], x_list[2], x_list[3], x_list[1]]
            else:
                return [x_list[2], x_list[3], x_list[1], x_list[0]]

    @classmethod
    def __get_areas(
        cls,
        image: MatLike,
        contours: list[MatLike],
        box: list[list[int]],
    ) -> NewData:
        """Get the area of all contours in the given image and save then to a json"""

        Logger.info("Getting areas of the contours.")

        delta_x_box = pitagoras_distance(box[0][0], box[1][0], box[0][1], box[1][1])
        delta_y_box = pitagoras_distance(box[0][0], box[3][0], box[0][1], box[3][1])
        area_px = delta_x_box * delta_y_box
        result = {
            "info": {
                "mm_to_px": cls.MM_PER_PIXEL,
                "mm_to_px_squared": cls.MM_PER_PIXEL_SQUARE,
                "box": {
                    "top_left": {"x": box[0][0], "y": box[0][1]},
                    "top_right": {"x": box[1][0], "y": box[1][1]},
                    "bottom_right": {"x": box[2][0], "y": box[2][1]},
                    "bottom_left": {"x": box[3][0], "y": box[3][1]},
                    "delta_mm": {
                        "x": delta_x_box * cls.MM_PER_PIXEL,
                        "y": delta_y_box * cls.MM_PER_PIXEL,
                    },
                    "delta_px": {"x": delta_x_box, "y": delta_y_box},
                    "area_px": area_px,
                    "area_mm": area_px * cls.MM_PER_PIXEL,
                },
            },
            "areas": [],
        }
        count = 0

        # * For debugging purposes
        white = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
        white.fill(255)

        for contour in contours:
            area = cv.contourArea(contour, oriented=True)

            if area < 0:
                continue

            m = cv.moments(contour)

            if m["m00"] == 0:
                continue

            cx = int(m["m10"] / m["m00"])
            cy = int(m["m01"] / m["m00"])

            mask = np.zeros((image.shape[0] + 2, image.shape[1] + 2), dtype=np.uint8)

            total, _, _, _ = cv.floodFill(
                image, mask, (cx, cy), (0, 0, 0), (0, 0, 0), (0, 0, 0)
            )

            # * For debugging purposes
            # if count == 0:
            #     Logger.debug(f"Total: {total}.")
            #     cv.imwrite(
            #         "./images/output/outputmask.png", (mask * 255).astype(np.uint8)
            #     )

            cv.circle(white, (cx, cy), 3, (0, 0, 0), -1)

            distance_px = {
                "top_left": pitagoras_distance(cx, box[0][0], cy, box[0][1]),
                "top_right": pitagoras_distance(cx, box[1][0], cy, box[1][1]),
                "bottom_right": pitagoras_distance(cx, box[2][0], cy, box[2][1]),
                "bottom_left": pitagoras_distance(cx, box[3][0], cy, box[3][1]),
            }

            # * Calculating the distance_top_left_px[x] using Herons formula to get the
            # * triangle area so we can calculate the height
            # * (the distance_top_left_px[x]).

            # * semi_perimeter = (
            # *     distance_px["top_left"] + distance_px["bottom_left"] + delta_y_box
            # * ) / 2

            # * triangle_area = (
            # *     semi_perimeter
            # *     * (semi_perimeter - distance_px["top_left"])
            # *     * (semi_perimeter - distance_px["bottom_left"])
            # *     * (semi_perimeter - delta_y_box)
            # * ).sqrt()

            # * distance_top_left_px_x = triangle_area * 2 / delta_y_box

            # * distance_top_left_px_y = (
            # *     pow(distance_px["top_left"], 2) - pow(distance_top_left_px_x, 2)
            # * ).sqrt()

            result["areas"].append(
                {
                    "id": count,
                    "area_mm": total * cls.MM_PER_PIXEL_SQUARE,
                    "area_px": total,
                    "distance_px": distance_px,
                    "distance_mm": {
                        "top_left": distance_px["top_left"] * cls.MM_PER_PIXEL,
                        "top_right": distance_px["top_right"] * cls.MM_PER_PIXEL,
                        "bottom_right": distance_px["bottom_right"] * cls.MM_PER_PIXEL,
                        "bottom_left": distance_px["bottom_left"] * cls.MM_PER_PIXEL,
                    },
                    # "distance_top_left_px": {
                    #     "x": distance_top_left_px_x,
                    #     "y": distance_top_left_px_y,
                    # },
                    # "distance_top_left_mm": {
                    #     "x": distance_top_left_px_x * cls.MM_PER_PIXEL,
                    #     "y": distance_top_left_px_y * cls.MM_PER_PIXEL,
                    # },
                }
            )

            count += 1

        result["info"]["total_areas"] = count

        Logger.debug(f"Area count: {count}.")

        result = cast(NewData, result)

        # * For debugging purposes
        cv.imwrite("./images/output/outputwhite.png", white)
        return result

    @classmethod
    def __save_json(cls, json_file: str, result: NewData):
        """Save the result to a json file."""

        Logger.info(f"Writing result to {json_file}.")

        try:
            with open(json_file, "w", encoding="utf=8") as f:
                dump(result, f, ensure_ascii=False, indent=None, cls=DecimalEncoder)
        except Exception as error:
            Logger.debug(f"Exception: {error}")
            # ! ERROR CODE 9
            Logger.err_exit(f"Failed writing to JSON {json_file}", code=9)
