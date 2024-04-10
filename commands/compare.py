import os
from decimal import Decimal
from json import dumps, load
from typing import Literal, cast

from .train import Train

from correct import Correct
from logger import Logger
from self_types import BaseData, ErrorAreas, Errors, NewData
from utils import (
    DecimalEncoder,
    fix_ids,
    herons_formula,
    object_hook_decimal,
    to_image_reference,
)


class Compare:

    @classmethod
    def run(
        cls,
        image_save_file: str,
        read_image: str,
        json_file: str,
        template_file: str,
    ):
        """
        Run the compare command, it will compare the image with the template and return
        the differences.

        Parameters
        ----------
        image_save_file : str
            File to save the image to if incorrect.

        read_image : str
            Path to image that will be read and processed if incorrectness are found.

        json_file : str
            Path and only name of the two JSON file that will be read or written,
            without the .json extension.

        template_file : str
            Path and only name of the JSON file that will be read or written, without
            the .json extension.
        """

        Logger.debug("Running compare command.")

        data = cls.__read_json(f"{json_file}.json")
        data = cast(NewData, data)

        template = cls.__read_json(f"{template_file}.json")
        template = cast(BaseData, template)

        error, order = cls.__compare(data, template)

        if error is None:
            Logger.info("No errors found.")
            template = Train.add_data(data, template, order)
            try:
                with open(f"{template_file}.json", "w") as file:
                    file.write(
                        dumps(
                            template,
                            indent=4,
                            ensure_ascii=False,
                            cls=DecimalEncoder,
                        )
                    )
            except Exception as error:
                Logger.debug(f"Exception: {error}")
                # ! ERROR CODE 9
                Logger.err_exit(f"Failed writing to JSON {template_file}.json.", code=9)
        else:
            Logger.info("Saving error data.")
            if error["areas"] is not None:
                for area in error["areas"]:
                    if area["id"] >= 0:
                        template["areas"][area["id"]]["failed"][
                            cast(
                                Literal["area", "center", "both", "unexistent"],
                                area["kind"],
                            )
                        ] += 1
            Correct.run(image_save_file, read_image, error)
            try:
                with open(f"{json_file}_errors.json", "w") as file:
                    file.write(
                        dumps(
                            error,
                            indent=4,
                            ensure_ascii=False,
                            cls=DecimalEncoder,
                        )
                    )
            except Exception as exception:
                Logger.debug(f"Exception: {exception}")
                # ! ERROR CODE 9
                Logger.err_exit("Failed writing to JSON errors.json.", code=9)
            try:
                with open(f"{template_file}_errors.json", "w") as file:
                    file.write(
                        dumps(
                            template,
                            indent=4,
                            ensure_ascii=False,
                            cls=DecimalEncoder,
                        )
                    )
            except Exception as exception:
                Logger.debug(f"Exception: {exception}")
                # ! ERROR CODE 9
                Logger.err_exit("Failed writing to JSON errors.json.", code=9)

    @classmethod
    def __compare(cls, data: NewData, template: BaseData) -> tuple[
        Errors | None,
        list[Literal["top_left", "top_right", "bottom_right", "bottom_left"]],
    ]:
        """
        Compare two files to see if they are the same piece, accepts the name of the
        file without the .json extension.
        """
        box: dict[Literal["correct_area_mm", "error_area_mm"], Decimal] | None = None
        order: list[Literal["top_left", "top_right", "bottom_right", "bottom_left"]] = [
            "top_left",
            "top_right",
            "bottom_right",
            "bottom_left",
        ]
        wrong = False
        error: Errors = {
            "info": {
                "constants_correct": {
                    "mm_to_px": True,
                    "mm_to_px_squared": True,
                },
                "rotate_correction": order,
                "template_total_areas": template["info"]["total_areas"],
                "sample_size": template["info"]["sample_size"],
            },
            "is_total_areas_correct": True,
            "areas": None,
            "box": box,
        }

        if data["info"]["mm_to_px"] != template["info"]["mm_to_px"]:
            Logger.critical("mm_to_px is not the same.")
            error["info"]["constants_correct"]["mm_to_px"] = False
            wrong = True

        if data["info"]["mm_to_px_squared"] != template["info"]["mm_to_px_squared"]:
            Logger.critical("mm_to_px_squared is not the same.")
            error["info"]["constants_correct"]["mm_to_px_squared"] = False
            wrong = True

        # Checking if the area of the box is in an acceptable range
        if not (
            data["info"]["box"]["area_px"]
            > template["info"]["stats"]["mean"]["area_px"]
            - template["info"]["stats"]["stdev"]["area_px"] * 3
        ) and (
            data["info"]["box"]["area_px"]
            < template["info"]["stats"]["mean"]["area_px"]
            + template["info"]["stats"]["stdev"]["area_px"] * 3
        ):
            Logger.critical("Box area is not in an acceptable range.")
            wrong = True
            error["box"] = {
                "correct_area_mm": template["info"]["stats"]["mean"]["area_mm"],
                "error_area_mm": template["info"]["stats"]["error"]["area_mm"],
            }

        # Checking if there are areas in the template and data
        if template["info"]["total_areas"] == 0 and data["info"]["total_areas"] == 0:
            Logger.critical("Template has no areas and data has no areas.")
            error["is_total_areas_correct"] = True
            if wrong:
                return error, order
            return None, order

        if template["info"]["total_areas"] == 0 and data["info"]["total_areas"] > 0:
            error["is_total_areas_correct"] = False

            for area in data["areas"]:
                distance_top_left_px_x, distance_top_left_px_y = herons_formula(
                    area["distance_px"][order[0]],
                    area["distance_px"][order[3]],
                    data["info"]["box"]["delta_px"]["y"],
                )

                cast(list[ErrorAreas], error["areas"]).append(
                    {
                        "id": -1,
                        "kind": "unexpected",
                        "correct_center_mm": {
                            "x": distance_top_left_px_x * template["info"]["mm_to_px"],
                            "y": distance_top_left_px_y * template["info"]["mm_to_px"],
                        },
                        "correct_center_px": to_image_reference(
                            data["info"]["box"]["top_left"],
                            data["info"]["box"]["bottom_left"],
                            {
                                "x": distance_top_left_px_x,
                                "y": distance_top_left_px_y,
                            },
                            data["info"]["box"]["delta_px"]["y"],
                        ),
                        "error_center_mm": {
                            "x": Decimal("0"),
                            "y": Decimal("0"),
                        },
                        "error_center_px": {
                            "x": 0,
                            "y": 0,
                        },
                        "correct_area_mm": Decimal("0"),
                        "correct_area_px": Decimal("0"),
                        "error_area_mm": Decimal("0"),
                        "error_area_px": Decimal("0"),
                    }
                )

            Logger.critical("Template has no areas and data has areas.")
            return error, order

        if template["info"]["total_areas"] > 0 and data["info"]["total_areas"] == 0:
            wrong = True
            error["is_total_areas_correct"] = False
            error["areas"] = []

            for area in template["areas"]:
                distance_top_left_px_x, distance_top_left_px_y = herons_formula(
                    area["mean"]["distance_px"][order[0]],
                    area["mean"]["distance_px"][order[3]],
                    template["info"]["stats"]["mean"]["delta_px"]["y"],
                )
                distance_top_left_px_x_error, distance_top_left_px_y_error = (
                    herons_formula(
                        area["error"]["distance_px"][order[0]],
                        area["error"]["distance_px"][order[3]],
                        template["info"]["stats"]["error"]["delta_px"]["y"],
                    )
                )

                cast(list[ErrorAreas], error["areas"]).append(
                    {
                        "id": area["id"],
                        "kind": "unexistent",
                        "correct_center_mm": {
                            "x": distance_top_left_px_x * template["info"]["mm_to_px"],
                            "y": distance_top_left_px_y * template["info"]["mm_to_px"],
                        },
                        "correct_center_px": to_image_reference(
                            data["info"]["box"]["top_left"],
                            data["info"]["box"]["bottom_left"],
                            {
                                "x": distance_top_left_px_x,
                                "y": distance_top_left_px_y,
                            },
                            data["info"]["box"]["delta_px"]["y"],
                        ),
                        "error_center_mm": {
                            "x": distance_top_left_px_x_error
                            * template["info"]["mm_to_px"],
                            "y": distance_top_left_px_y_error
                            * template["info"]["mm_to_px"],
                        },
                        "error_center_px": to_image_reference(
                            data["info"]["box"]["top_left"],
                            data["info"]["box"]["bottom_left"],
                            {
                                "x": distance_top_left_px_x_error,
                                "y": distance_top_left_px_y_error,
                            },
                            data["info"]["box"]["delta_px"]["y"],
                        ),
                        "correct_area_mm": area["mean"]["area_mm"],
                        "correct_area_px": area["mean"]["area_px"],
                        "error_area_mm": area["error"]["area_mm"],
                        "error_area_px": area["error"]["area_px"],
                    }
                )

            Logger.critical("Template has areas and data has no areas.")
            return error, order

        if template["info"]["total_areas"] < data["info"]["total_areas"]:
            wrong = True
            error["is_total_areas_correct"] = False

            Logger.critical("Template has less areas than data.")

        # Getting a reference point and order for the areas
        data["areas"], order = fix_ids(template["areas"], data["areas"])
        template["areas"] = sorted(template["areas"], key=lambda x: x["id"])

        print([area["id"] for area in data["areas"]])
        print([area["id"] for area in template["areas"]])

        error["info"]["rotate_correction"] = order

        temp_errors: list[ErrorAreas] = []
        # Checking all areas
        for new_area in data["areas"]:
            # Checking if the center mm is in an acceptable range

            if new_area["id"] >= 0:
                temp: ErrorAreas | None = None
                area = template["areas"][new_area["id"]]
                if (
                    (
                        new_area["distance_px"][order[0]]
                        > area["mean"]["distance_px"]["top_left"]
                        + area["stdev"]["distance_px"]["top_left"] * 3
                    )
                    or (
                        new_area["distance_px"][order[0]]
                        < area["mean"]["distance_px"]["top_left"]
                        - area["stdev"]["distance_px"]["top_left"] * 3
                    )
                    or (
                        new_area["distance_px"][order[1]]
                        > area["mean"]["distance_px"]["top_right"]
                        + area["stdev"]["distance_px"]["top_right"] * 3
                    )
                    or (
                        new_area["distance_px"][order[1]]
                        < area["mean"]["distance_px"]["top_right"]
                        - area["stdev"]["distance_px"]["top_right"] * 3
                    )
                ):
                    Logger.critical(
                        f"Area {area['id']} is not in an acceptable range for it's"
                        + " center position."
                    )

                    distance_top_left_px_x, distance_top_left_px_y = herons_formula(
                        area["mean"]["distance_px"][order[0]],
                        area["mean"]["distance_px"][order[3]],
                        template["info"]["stats"]["mean"]["delta_px"]["y"],
                    )

                    distance_top_left_px_x_error, distance_top_left_px_y_error = (
                        herons_formula(
                            area["error"]["distance_px"][order[0]],
                            area["error"]["distance_px"][order[3]],
                            template["info"]["stats"]["error"]["delta_px"]["y"],
                        )
                    )

                    temp = {
                        "id": area["id"],
                        "kind": "center",
                        "correct_center_mm": {
                            "x": distance_top_left_px_x * template["info"]["mm_to_px"],
                            "y": distance_top_left_px_y * template["info"]["mm_to_px"],
                        },
                        "correct_center_px": to_image_reference(
                            data["info"]["box"]["top_left"],
                            data["info"]["box"]["bottom_left"],
                            {
                                "x": distance_top_left_px_x,
                                "y": distance_top_left_px_y,
                            },
                            data["info"]["box"]["delta_px"]["y"],
                        ),
                        "error_center_mm": {
                            "x": distance_top_left_px_x_error
                            * template["info"]["mm_to_px"],
                            "y": distance_top_left_px_y_error
                            * template["info"]["mm_to_px"],
                        },
                        "error_center_px": to_image_reference(
                            data["info"]["box"]["top_left"],
                            data["info"]["box"]["bottom_left"],
                            {
                                "x": distance_top_left_px_x_error,
                                "y": distance_top_left_px_y_error,
                            },
                            data["info"]["box"]["delta_px"]["y"],
                        ),
                        "correct_area_mm": area["mean"]["area_mm"],
                        "correct_area_px": area["mean"]["area_px"],
                        "error_area_mm": area["error"]["area_mm"],
                        "error_area_px": area["error"]["area_px"],
                    }

                # Checking if the area mm is in an acceptable range
                if (
                    new_area["area_px"]
                    > area["mean"]["area_px"] + area["stdev"]["area_px"] * 3
                ) or (
                    new_area["area_px"]
                    < area["mean"]["area_px"] - area["stdev"]["area_px"] * 3
                ):
                    Logger.critical(
                        f"Area {area['id']} is not in an acceptable range for it's area"
                        + " size."
                    )

                    if temp is None:
                        distance_top_left_px_x, distance_top_left_px_y = herons_formula(
                            area["mean"]["distance_px"][order[0]],
                            area["mean"]["distance_px"][order[3]],
                            template["info"]["stats"]["mean"]["delta_px"]["y"],
                        )
                        distance_top_left_px_x_error, distance_top_left_px_y_error = (
                            herons_formula(
                                area["error"]["distance_px"][order[0]],
                                area["error"]["distance_px"][order[3]],
                                template["info"]["stats"]["error"]["delta_px"]["y"],
                            )
                        )

                        temp = {
                            "id": area["id"],
                            "kind": "center",
                            "correct_center_mm": {
                                "x": distance_top_left_px_x
                                * template["info"]["mm_to_px"],
                                "y": distance_top_left_px_y
                                * template["info"]["mm_to_px"],
                            },
                            "correct_center_px": to_image_reference(
                                data["info"]["box"]["top_left"],
                                data["info"]["box"]["bottom_left"],
                                {
                                    "x": distance_top_left_px_x,
                                    "y": distance_top_left_px_y,
                                },
                                data["info"]["box"]["delta_px"]["y"],
                            ),
                            "error_center_mm": {
                                "x": distance_top_left_px_x_error
                                * template["info"]["mm_to_px"],
                                "y": distance_top_left_px_y_error
                                * template["info"]["mm_to_px"],
                            },
                            "error_center_px": to_image_reference(
                                data["info"]["box"]["top_left"],
                                data["info"]["box"]["bottom_left"],
                                {
                                    "x": distance_top_left_px_x_error,
                                    "y": distance_top_left_px_y_error,
                                },
                                data["info"]["box"]["delta_px"]["y"],
                            ),
                            "correct_area_mm": area["mean"]["area_mm"],
                            "correct_area_px": area["mean"]["area_px"],
                            "error_area_mm": area["error"]["area_mm"],
                            "error_area_px": area["error"]["area_px"],
                        }
                    else:
                        temp["kind"] = "both"

            else:
                distance_top_left_px_x, distance_top_left_px_y = herons_formula(
                    new_area["distance_px"][order[0]],
                    new_area["distance_px"][order[3]],
                    data["info"]["box"]["delta_px"]["y"],
                )

                temp = {
                    "id": new_area["id"],
                    "kind": "unexpected",
                    "correct_center_mm": {
                        "x": distance_top_left_px_x * template["info"]["mm_to_px"],
                        "y": distance_top_left_px_y * template["info"]["mm_to_px"],
                    },
                    "correct_center_px": to_image_reference(
                        data["info"]["box"]["top_left"],
                        data["info"]["box"]["bottom_left"],
                        {
                            "x": distance_top_left_px_x,
                            "y": distance_top_left_px_y,
                        },
                        data["info"]["box"]["delta_px"]["y"],
                    ),
                    "error_center_mm": {
                        "x": Decimal("0"),
                        "y": Decimal("0"),
                    },
                    "error_center_px": {
                        "x": 0,
                        "y": 0,
                    },
                    "correct_area_mm": Decimal("0"),
                    "correct_area_px": Decimal("0"),
                    "error_area_mm": Decimal("0"),
                    "error_area_px": Decimal("0"),
                }

            if temp is not None:
                temp_errors.append(temp)

        if data["info"]["total_areas"] < template["info"]["total_areas"]:
            error["is_total_areas_correct"] = False

            not_taken = [
                x
                for x in range(template["info"]["total_areas"])
                if x not in [area["id"] for area in data["areas"]]
            ]

            for i in not_taken:
                distance_top_left_px_x, distance_top_left_px_y = herons_formula(
                    template["areas"][i]["mean"]["distance_px"][order[0]],
                    template["areas"][i]["mean"]["distance_px"][order[3]],
                    template["info"]["stats"]["mean"]["delta_px"]["y"],
                )
                distance_top_left_px_x_error, distance_top_left_px_y_error = (
                    herons_formula(
                        template["areas"][i]["error"]["distance_px"][order[0]],
                        template["areas"][i]["error"]["distance_px"][order[3]],
                        template["info"]["stats"]["error"]["delta_px"]["y"],
                    )
                )

                temp_errors.append(
                    {
                        "id": template["areas"][i]["id"],
                        "kind": "unexistent",
                        "correct_center_mm": {
                            "x": distance_top_left_px_x * template["info"]["mm_to_px"],
                            "y": distance_top_left_px_y * template["info"]["mm_to_px"],
                        },
                        "correct_center_px": to_image_reference(
                            data["info"]["box"]["top_left"],
                            data["info"]["box"]["bottom_left"],
                            {
                                "x": distance_top_left_px_x,
                                "y": distance_top_left_px_y,
                            },
                            data["info"]["box"]["delta_px"]["y"],
                        ),
                        "error_center_mm": {
                            "x": distance_top_left_px_x_error
                            * template["info"]["mm_to_px"],
                            "y": distance_top_left_px_y_error
                            * template["info"]["mm_to_px"],
                        },
                        "error_center_px": to_image_reference(
                            data["info"]["box"]["top_left"],
                            data["info"]["box"]["bottom_left"],
                            {
                                "x": distance_top_left_px_x_error,
                                "y": distance_top_left_px_y_error,
                            },
                            data["info"]["box"]["delta_px"]["y"],
                        ),
                        "correct_area_mm": template["areas"][i]["mean"]["area_mm"],
                        "correct_area_px": template["areas"][i]["mean"]["area_px"],
                        "error_area_mm": template["areas"][i]["error"]["area_mm"],
                        "error_area_px": template["areas"][i]["error"]["area_px"],
                    }
                )

        if len(temp_errors) > 0 or wrong:
            error["areas"] = temp_errors
            return error, order

        return None, order

    @classmethod
    def __read_json(cls, json_name: str):
        """Read a json file and return it as a dict."""

        if not os.path.isfile(json_name):
            # ! ERROR CODE 10
            Logger.err_exit(f"JSON {json_name} not found.", code=10)

        try:
            with open(json_name, "r") as file:
                return load(
                    file,
                    object_hook=object_hook_decimal,
                )
        except Exception as error:
            Logger.debug(f"{error}")
            # ! ERROR CODE 11
            Logger.err_exit(f"Unable to read JSON {json_name}.", code=11)
