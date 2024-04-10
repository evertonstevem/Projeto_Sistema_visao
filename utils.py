from copy import deepcopy
from decimal import Decimal
from json import JSONEncoder
from math import acos, sin
from re import match
from typing import Dict, Literal, TypeVar, cast

from self_types import Area, BaseArea


class DecimalEncoder(JSONEncoder):
    """JSON encoder for Decimal numbers."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return JSONEncoder.default(self, obj)


# ^+?(?=.*[1-9])\d*(?:\.\d*)?$ # Matches any number greater than 0
# ^[-+]?\d*(\.\d*)?$ # Matches any number


def object_hook_decimal(data: Dict):
    """Convert string numbers to Decimal. For the object_hook parameter in json.load."""
    for key, value in data.items():
        new_value = value
        if type(value) is str:
            if match(r"^[-\+]?\d*(\.\d*)?$", value):
                if "-" in value:
                    raise ValueError("Negative numbers are not allowed")
                new_value = Decimal(value)
        data[key] = new_value
    return data


def pitagoras_distance(
    point_0_x: int | Decimal,
    point_1_x: int | Decimal,
    point_0_y: int | Decimal,
    point_1_y: int | Decimal,
) -> Decimal:
    """
    Calculate the distance between two points.

    Parameters
    ----------
    point_0_x : int
        The x coordinate of the first point.
    point_1_x : int
        The x coordinate of the second point.
    point_0_y : int
        The y coordinate of the first point.
    point_1_y : int
        The y coordinate of the second point.

    Returns
    -------
    Decimal
        The distance between the two points.
    """

    return Decimal(
        pow((point_1_x - point_0_x), 2) + pow((point_1_y - point_0_y), 2)
    ).sqrt()


T = TypeVar("T")


def switch(array: list[T]) -> list[T]:
    return [array[1], array[2], array[3], array[0]]


def to_image_reference(
    top_left: dict[Literal["x", "y"], int],
    bottom_left: dict[Literal["x", "y"], int],
    delta: dict[Literal["x", "y"], Decimal],
    delta_y: Decimal,
) -> dict[Literal["x", "y"], int]:
    """
    Get's a point position relative to the image cartesian plane based on it's position
    relative to a rotated box top left point.

    Parameters
    ----------
    top_left : dict[Literal["x", "y"], int]
        The top left point of the rotated box.
    bottom_left : dict[Literal["x", "y"], int]
        The bottom left point of the rotated box.
    delta : dict[Literal["x", "y"], Decimal]
        The delta between the top left point and the point to be converted relative to
        the rotated box.

    Returns
    -------
    dict[Literal["x", "y"], Decimal]
        The point position relative to the image cartesian plane.
    """

    mid_point_delta = {"x": Decimal(0), "y": Decimal(0)}
    point_delta_to_mid = {"x": Decimal(0), "y": Decimal(0)}

    if top_left["x"] < bottom_left["x"]:
        angle_cos = Decimal(0)
        distance_delta_x = abs(top_left["x"] - bottom_left["x"])
        angle_cos = Decimal(f"{distance_delta_x / delta_y}")
        angle = Decimal(acos(angle_cos))
        mid_point_delta["x"] = delta["y"] * angle_cos
        mid_point_delta["y"] = delta["y"] * Decimal(sin(angle))
        point_delta_to_mid["x"] = delta["x"] * Decimal(sin(angle))
        point_delta_to_mid["y"] = delta["x"] * angle_cos

        return {
            "x": round(top_left["x"] + mid_point_delta["x"] + point_delta_to_mid["x"]),
            "y": round(top_left["y"] + mid_point_delta["y"] - point_delta_to_mid["y"]),
        }

    elif top_left["x"] > bottom_left["x"]:
        angle_cos = Decimal(0)
        distance_delta_y = abs(top_left["y"] - bottom_left["y"])
        angle_cos = Decimal(f"{distance_delta_y / delta_y}")
        angle = Decimal(acos(angle_cos))
        mid_point_delta["x"] = delta["y"] * Decimal(sin(angle))
        mid_point_delta["y"] = delta["y"] * angle_cos
        point_delta_to_mid["x"] = delta["x"] * angle_cos
        point_delta_to_mid["y"] = delta["x"] * Decimal(sin(angle))

        return {
            "x": round(top_left["x"] - mid_point_delta["x"] + point_delta_to_mid["x"]),
            "y": round(top_left["y"] + mid_point_delta["y"] + point_delta_to_mid["y"]),
        }

    else:
        return {
            "x": round(top_left["x"] + delta["x"]),
            "y": round(top_left["y"] + delta["y"]),
        }


def fix_ids(areas: list[BaseArea], new_areas: list[Area]) -> tuple[
    list[Area],
    list[Literal["top_left", "top_right", "bottom_right", "bottom_left"]],
]:
    """
    Fix the ids of the new data areas to match the template data areas.

    Parameters
    ----------
    areas : list[BaseArea]
        The template areas.
    new_areas : list[Area]
        The new data areas.

    Returns
    -------
    tuple[list[Area], list[Literal["top_left", "top_right", "bottom_right",
    "bottom_left"]]]
        The new data areas with the fixed ids and the new order.
    """

    order: list[Literal["top_left", "top_right", "bottom_right", "bottom_left"]] = [
        "top_left",
        "top_right",
        "bottom_right",
        "bottom_left",
    ]

    if len(areas) == 0:
        return new_areas, order

    if len(areas) < 2:
        temp_order_diff_0 = (
            abs(
                new_areas[0]["distance_px"][order[0]]
                - areas[0]["mean"]["distance_px"]["top_left"]
            )
            + abs(
                new_areas[0]["distance_px"][order[1]]
                - areas[0]["mean"]["distance_px"]["top_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[2]]
                - areas[0]["mean"]["distance_px"]["bottom_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[3]]
                - areas[0]["mean"]["distance_px"]["bottom_left"]
            )
        )
        temp_order_diff_1 = (
            abs(
                new_areas[0]["distance_px"][order[1]]
                - areas[0]["mean"]["distance_px"]["top_left"]
            )
            + abs(
                new_areas[0]["distance_px"][order[2]]
                - areas[0]["mean"]["distance_px"]["top_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[3]]
                - areas[0]["mean"]["distance_px"]["bottom_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[0]]
                - areas[0]["mean"]["distance_px"]["bottom_left"]
            )
        )
        temp_order_diff_2 = (
            abs(
                new_areas[0]["distance_px"][order[2]]
                - areas[0]["mean"]["distance_px"]["top_left"]
            )
            + abs(
                new_areas[0]["distance_px"][order[3]]
                - areas[0]["mean"]["distance_px"]["top_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[0]]
                - areas[0]["mean"]["distance_px"]["bottom_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[1]]
                - areas[0]["mean"]["distance_px"]["bottom_left"]
            )
        )
        temp_order_diff_3 = (
            abs(
                new_areas[0]["distance_px"][order[3]]
                - areas[0]["mean"]["distance_px"]["top_left"]
            )
            + abs(
                new_areas[0]["distance_px"][order[0]]
                - areas[0]["mean"]["distance_px"]["top_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[1]]
                - areas[0]["mean"]["distance_px"]["bottom_right"]
            )
            + abs(
                new_areas[0]["distance_px"][order[2]]
                - areas[0]["mean"]["distance_px"]["bottom_left"]
            )
        )

        ordering = min(
            [
                [temp_order_diff_0, 0],
                [temp_order_diff_1, 1],
                [temp_order_diff_2, 2],
                [temp_order_diff_3, 3],
            ]
        )

        for i in range(cast(int, ordering[1])):
            order = switch(order)

        new_areas[0]["id"] = areas[0]["id"]

        return new_areas, order

    for new_area in new_areas:
        new_area["id"] = -1

    areas = sorted(areas, key=lambda x: x["id"])
    temp_areas = deepcopy(areas)

    order_diffs = [
        [
            [Decimal("Infinity"), 0],
            [Decimal("Infinity"), 0],
            [Decimal("Infinity"), 0],
            [Decimal("Infinity"), 0],
        ],
        [
            [Decimal("Infinity"), -1],
            [Decimal("Infinity"), -1],
            [Decimal("Infinity"), -1],
            [Decimal("Infinity"), -1],
        ],
    ]

    for i, new_area in enumerate(new_areas[:2]):
        for idx, area in enumerate(temp_areas):
            temp_order_diff_0 = (
                abs(
                    new_area["distance_px"][order[0]]
                    - area["mean"]["distance_px"]["top_left"]
                )
                + abs(
                    new_area["distance_px"][order[1]]
                    - area["mean"]["distance_px"]["top_right"]
                )
                + abs(
                    new_area["distance_px"][order[2]]
                    - area["mean"]["distance_px"]["bottom_right"]
                )
                + abs(
                    new_area["distance_px"][order[3]]
                    - area["mean"]["distance_px"]["bottom_left"]
                )
            )
            temp_order_diff_1 = (
                abs(
                    new_area["distance_px"][order[1]]
                    - area["mean"]["distance_px"]["top_left"]
                )
                + abs(
                    new_area["distance_px"][order[2]]
                    - area["mean"]["distance_px"]["top_right"]
                )
                + abs(
                    new_area["distance_px"][order[3]]
                    - area["mean"]["distance_px"]["bottom_right"]
                )
                + abs(
                    new_area["distance_px"][order[0]]
                    - area["mean"]["distance_px"]["bottom_left"]
                )
            )
            temp_order_diff_2 = (
                abs(
                    new_area["distance_px"][order[2]]
                    - area["mean"]["distance_px"]["top_left"]
                )
                + abs(
                    new_area["distance_px"][order[3]]
                    - area["mean"]["distance_px"]["top_right"]
                )
                + abs(
                    new_area["distance_px"][order[0]]
                    - area["mean"]["distance_px"]["bottom_right"]
                )
                + abs(
                    new_area["distance_px"][order[1]]
                    - area["mean"]["distance_px"]["bottom_left"]
                )
            )
            temp_order_diff_3 = (
                abs(
                    new_area["distance_px"][order[3]]
                    - area["mean"]["distance_px"]["top_left"]
                )
                + abs(
                    new_area["distance_px"][order[0]]
                    - area["mean"]["distance_px"]["top_right"]
                )
                + abs(
                    new_area["distance_px"][order[1]]
                    - area["mean"]["distance_px"]["bottom_right"]
                )
                + abs(
                    new_area["distance_px"][order[2]]
                    - area["mean"]["distance_px"]["bottom_left"]
                )
            )

            if temp_order_diff_0 < order_diffs[i][0][0]:
                order_diffs[i][0][0] = temp_order_diff_0
                order_diffs[i][0][1] = idx

            if temp_order_diff_1 < order_diffs[i][1][0]:
                order_diffs[i][1][0] = temp_order_diff_1
                order_diffs[i][1][1] = idx

            if temp_order_diff_2 < order_diffs[i][2][0]:
                order_diffs[i][2][0] = temp_order_diff_2
                order_diffs[i][2][1] = idx

            if temp_order_diff_3 < order_diffs[i][3][0]:
                order_diffs[i][3][0] = temp_order_diff_3
                order_diffs[i][3][1] = idx

    ordering = min(
        [
            [
                order_diffs[0][i][0] + order_diffs[1][i][0],
                order_diffs[0][i][1],
                order_diffs[1][i][1],
                i,
            ]
            for i in range(4)
        ],
        key=lambda x: x[0],
    )

    for i in range(ordering[3]):
        order = switch(order)

    new_areas[0]["id"] = temp_areas[ordering[1]]["id"]
    new_areas[1]["id"] = temp_areas[ordering[2]]["id"]

    if ordering[1] > ordering[2]:
        temp_areas.pop(ordering[1])
        temp_areas.pop(ordering[2])
    else:
        temp_areas.pop(ordering[2])
        temp_areas.pop(ordering[1])

    for new_area in new_areas[2:]:
        closest = 0
        diff = Decimal("Infinity")
        for area in temp_areas:
            temp_diff = abs(
                new_area["distance_px"][order[3]]
                - area["mean"]["distance_px"]["bottom_left"]
            ) + abs(
                new_area["distance_px"][order[0]]
                - area["mean"]["distance_px"]["top_left"]
            )

            if temp_diff < diff:
                closest = area["id"]
                diff = temp_diff

        if len(temp_areas) > 0:
            new_area["id"] = closest
            temp_areas = [area for area in temp_areas if area["id"] != closest]

    if len(areas) < len(new_areas):
        for i, new_area in enumerate(new_areas[len(areas) :]):
            closest = 0
            diff = Decimal("Infinity")
            for area in areas:
                temp_diff = abs(
                    new_area["distance_px"][order[3]]
                    - area["mean"]["distance_px"]["bottom_left"]
                ) + abs(
                    new_area["distance_px"][order[0]]
                    - area["mean"]["distance_px"]["top_left"]
                )

                if temp_diff < diff:
                    closest = area["id"]
                    diff = temp_diff

            base_new_area = [
                [i, area] for i, area in enumerate(new_areas) if area["id"] == closest
            ][0]

            old_diff = abs(
                base_new_area[1]["distance_px"][order[3]]
                - areas[closest]["mean"]["distance_px"]["bottom_left"]
            ) + abs(
                base_new_area[1]["distance_px"][order[0]]
                - areas[closest]["mean"]["distance_px"]["top_left"]
            )

            if diff < old_diff:
                new_area["id"] = closest
                new_areas[base_new_area[0]]["id"] = -1

    return new_areas, order


def herons_formula(
    top_left_distance: Decimal, bottom_left_distance: Decimal, delta_y
) -> tuple[Decimal, Decimal]:
    """
    Calculate the delta x and delta y of the point according to it's distance to the
    top left and bottom left extreme points by using Heron's formula.

    Parameters
    ----------
    top_left_distance : Decimal
        The distance between the point and the top left extreme point.
    bottom_left_distance : Decimal
        The distance between the point and the bottom left extreme point.
    delta_y : Decimal
        The distance between the top left and bottom left extreme points.

    Returns
    -------
    tuple[Decimal, Decimal]
        The delta x and delta y of the point according to the box they are a part of.
    """
    semi_perimeter = (top_left_distance + bottom_left_distance + delta_y) / 2

    triangle_area = (
        semi_perimeter
        * (semi_perimeter - top_left_distance)
        * (semi_perimeter - bottom_left_distance)
        * (semi_perimeter - delta_y)
    )

    if triangle_area < 0:
        return Decimal("0"), Decimal("0")

    distance_top_left_px_x = triangle_area.sqrt() * 2 / delta_y

    distance_top_left_px_y = (
        pow(top_left_distance, 2) - pow(distance_top_left_px_x, 2)
    ).sqrt()

    return distance_top_left_px_x, distance_top_left_px_y
