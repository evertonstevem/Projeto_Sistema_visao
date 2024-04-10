from decimal import Decimal
from json import dump, load
from os import path
from typing import Literal

from logger import Logger
from self_types import Area, BaseArea, BaseData, BaseInfo, Info, NewData
from utils import DecimalEncoder, fix_ids, object_hook_decimal


class Train:

    # PX_ARTIFICIAL_ERROR = 16
    # CANTOR_ARTIFICIAL_ERROR = (160**2) // 2

    @classmethod
    def run(cls, json_file: str, template_file: str):
        """
        Run the train command, there must be 10 json files with the name
        '<name>_{01-10}.json'.

        The files passed for training must be of the same piece and be in the same
        if the pieces are not in the same rotation, the training will not be correct.
        """

        Logger.debug("Running train command.")

        base: BaseData | None = None
        order: list[Literal["top_left", "top_right", "bottom_right", "bottom_left"]] = [
            "top_left",
            "top_right",
            "bottom_right",
            "bottom_left",
        ]

        for i in range(1, 11):
            file = f"{json_file}_{i:02d}.json"
            if not path.isfile(file):
                # ! ERROR CODE 10
                Logger.err_exit(f"JSON {file} not found.", code=10)

            data = cls.__get_new_data(file)

            if base is None:
                base = {
                    "info": {
                        "mm_to_px": data["info"]["mm_to_px"],
                        "mm_to_px_squared": data["info"]["mm_to_px_squared"],
                        "stats": {
                            "mean": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "delta_mm": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                                "delta_px": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                            },
                            "variance": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "delta_mm": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                                "delta_px": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                            },
                            "stdev": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "delta_mm": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                                "delta_px": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                            },
                            "error": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "delta_mm": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                                "delta_px": {
                                    "x": Decimal(0),
                                    "y": Decimal(0),
                                },
                            },
                        },
                        "total_areas": data["info"]["total_areas"],
                        "sample_size": 0,
                    },
                    "areas": [
                        {
                            "id": x,
                            "failed": {
                                "area": 0,
                                "both": 0,
                                "unexistent": 0,
                                "center": 0,
                            },
                            "mean": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "distance_px": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                                "distance_mm": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                            },
                            "variance": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "distance_px": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                                "distance_mm": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                            },
                            "stdev": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "distance_px": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                                "distance_mm": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                            },
                            "error": {
                                "area_mm": Decimal(0),
                                "area_px": Decimal(0),
                                "distance_px": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                                "distance_mm": {
                                    "top_left": Decimal(0),
                                    "top_right": Decimal(0),
                                    "bottom_right": Decimal(0),
                                    "bottom_left": Decimal(0),
                                },
                            },
                        }
                        for x in range(data["info"]["total_areas"])
                    ],
                }
                base["areas"] = sorted(base["areas"], key=lambda x: x["id"])
                base = cls.add_data(data, base, order)
                continue

            if base["info"]["total_areas"] != data["info"]["total_areas"]:
                # ! ERROR CODE 12
                Logger.err_exit(
                    f"Number of areas between {file} and template does not " + "match.",
                    code=12,
                )

            if base["info"]["mm_to_px"] != data["info"]["mm_to_px"]:
                # ! ERROR CODE 14
                Logger.err_exit(
                    "TRAINING | Incorrect pieces constants (mm_to_px_squared)",
                    code=14,
                )

            if base["info"]["mm_to_px_squared"] != data["info"]["mm_to_px_squared"]:
                # ! ERROR CODE 14
                Logger.err_exit(
                    "TRAINING | Incorrect pieces constants (mm_to_px_squared)",
                    code=14,
                )

            Logger.info("Correcting id for the new data")
            data["areas"], order = fix_ids(base["areas"], data["areas"])
            base["areas"] = sorted(base["areas"], key=lambda x: x["id"])

            base = cls.add_data(data, base, order)

        Logger.info("Saving template data.")

        try:
            with open(f"{template_file}.json", "w") as file:
                dump(
                    base,
                    file,
                    indent=4,
                    ensure_ascii=False,
                    cls=DecimalEncoder,
                )
        except Exception as error:
            Logger.debug(f"Exception: {error}")
            # ! ERROR CODE 9
            Logger.err_exit(f"Failed writing to JSON {template_file}.json.", code=9)

    @classmethod
    def __get_new_data(cls, json_file: str) -> NewData:
        """Get the new data from the JSON file."""

        Logger.info("Getting new data from JSON file.")

        data = None
        try:
            with open(json_file, "r") as file:
                data = load(
                    file,
                    object_hook=object_hook_decimal,
                )
        except Exception as error:
            Logger.debug(f"{error}")
            # ! ERROR CODE 11
            Logger.err_exit(f"Unable to read JSON {json_file}.", code=11)

        return data

    @classmethod
    def add_data(
        cls,
        data: NewData,
        base: BaseData,
        order: list[Literal["top_left", "top_right", "bottom_right", "bottom_left"]],
    ) -> BaseData:
        """
        Add the data to the template data.

        The data must been guaranteed to be correct before calling this function.

        Also the base data must be sorted by the id of the areas.

        """

        Logger.info("Updating template data.")

        Logger.info("Adding data to template data.")

        old_sample_size = base["info"]["sample_size"]

        base["info"]["sample_size"] += 1
        n_sqrt = Decimal(base["info"]["sample_size"]).sqrt()

        # !Calculate the stats for the info
        base["info"] = cls.__calc_info_stats(base["info"], data["info"])

        for new_area in data["areas"]:

            area = base["areas"][new_area["id"]]

            area = cls.__calc_stats_distances(base["info"], area, new_area, order)

            old_mean_area_mm = area["mean"]["area_mm"]
            old_mean_area_px = area["mean"]["area_px"]

            area["mean"]["area_mm"] = cls.__calc_mean(
                area["mean"]["area_mm"],
                base["info"]["sample_size"],
                new_area["area_mm"],
            )
            area["mean"]["area_px"] = cls.__calc_mean(
                area["mean"]["area_px"],
                base["info"]["sample_size"],
                new_area["area_px"],
            )

            area["variance"]["area_mm"] = cls.__calc_variance(
                area["variance"]["area_mm"],
                old_mean_area_mm,
                area["mean"]["area_mm"],
                old_sample_size,
                new_area["area_mm"],
            )
            area["variance"]["area_px"] = cls.__calc_variance(
                area["variance"]["area_px"],
                old_mean_area_px,
                area["mean"]["area_px"],
                old_sample_size,
                new_area["area_px"],
            )

            area["stdev"]["area_mm"] = area["variance"]["area_mm"].sqrt()
            area["stdev"]["area_px"] = area["variance"]["area_px"].sqrt()

            area["error"]["area_mm"] = area["stdev"]["area_mm"] / n_sqrt
            area["error"]["area_px"] = area["stdev"]["area_px"] / n_sqrt

        Logger.info("Updated template data")
        return base

    @classmethod
    def __calc_mean(
        cls, old_mean: Decimal, n: int, new_element: Decimal | int
    ) -> Decimal:
        """Calculate the new mean of the data based on the old one."""

        return (old_mean * (n - 1) + new_element) / n

    @classmethod
    def __calc_variance(
        cls,
        old_variance: Decimal,
        old_mean: Decimal,
        new_mean: Decimal,
        old_n: int,
        new_element: Decimal | int,
    ) -> Decimal:
        """Calculate the new variance of the data based on the old one."""

        if old_n == 0:
            return Decimal(0)

        return (
            ((old_n - 1) * old_variance)
            + ((new_element - old_mean) * (new_element - new_mean))
        ) / old_n

    @classmethod
    def __calc_stats_distances(
        cls,
        base_data_info: BaseInfo,
        area: BaseArea,
        data: Area,
        order: list[Literal["top_left", "top_right", "bottom_right", "bottom_left"]],
    ) -> BaseArea:
        """Calculate the stats for the distances."""

        old_sample_size = base_data_info["sample_size"] - 1
        n_sqrt = Decimal(base_data_info["sample_size"]).sqrt()
        for metric in ["px", "mm"]:
            # !Old means
            means = {
                "top_left": area["mean"][f"distance_{metric}"]["top_left"],
                "top_right": area["mean"][f"distance_{metric}"]["top_right"],
                "bottom_right": area["mean"][f"distance_{metric}"]["bottom_right"],
                "bottom_left": area["mean"][f"distance_{metric}"]["bottom_left"],
            }

            # !Calculate the mean for the distances
            area["mean"][f"distance_{metric}"]["top_left"] = cls.__calc_mean(
                area["mean"][f"distance_{metric}"]["top_left"],
                base_data_info["sample_size"],
                data[f"distance_{metric}"][order[0]],
            )
            area["mean"][f"distance_{metric}"]["top_right"] = cls.__calc_mean(
                area["mean"][f"distance_{metric}"]["top_right"],
                base_data_info["sample_size"],
                data[f"distance_{metric}"][order[1]],
            )
            area["mean"][f"distance_{metric}"]["bottom_right"] = cls.__calc_mean(
                area["mean"][f"distance_{metric}"]["bottom_right"],
                base_data_info["sample_size"],
                data[f"distance_{metric}"][order[2]],
            )
            area["mean"][f"distance_{metric}"]["bottom_left"] = cls.__calc_mean(
                area["mean"][f"distance_{metric}"]["bottom_left"],
                base_data_info["sample_size"],
                data[f"distance_{metric}"][order[3]],
            )

            # !Calculate the variance for the distances
            area["variance"][f"distance_{metric}"]["top_left"] = cls.__calc_variance(
                area["variance"][f"distance_{metric}"]["top_left"],
                means["top_left"],
                area["mean"][f"distance_{metric}"]["top_left"],
                old_sample_size,
                data[f"distance_{metric}"][order[0]],
            )
            area["variance"][f"distance_{metric}"]["top_right"] = cls.__calc_variance(
                area["variance"][f"distance_{metric}"]["top_right"],
                means["top_right"],
                area["mean"][f"distance_{metric}"]["top_right"],
                old_sample_size,
                data[f"distance_{metric}"][order[1]],
            )
            area["variance"][f"distance_{metric}"]["bottom_right"] = (
                cls.__calc_variance(
                    area["variance"][f"distance_{metric}"]["bottom_right"],
                    means["bottom_right"],
                    area["mean"][f"distance_{metric}"]["bottom_right"],
                    old_sample_size,
                    data[f"distance_{metric}"][order[2]],
                )
            )
            area["variance"][f"distance_{metric}"]["bottom_left"] = cls.__calc_variance(
                area["variance"][f"distance_{metric}"]["bottom_left"],
                means["bottom_left"],
                area["mean"][f"distance_{metric}"]["bottom_left"],
                base_data_info["sample_size"],
                data[f"distance_{metric}"][order[3]],
            )

            # !Calculate the standard deviation for the distances
            area["stdev"][f"distance_{metric}"]["top_left"] = area["variance"][
                f"distance_{metric}"
            ]["top_left"].sqrt()
            area["stdev"][f"distance_{metric}"]["top_right"] = area["variance"][
                f"distance_{metric}"
            ]["top_right"].sqrt()
            area["stdev"][f"distance_{metric}"]["bottom_right"] = area["variance"][
                f"distance_{metric}"
            ]["bottom_right"].sqrt()
            area["stdev"][f"distance_{metric}"]["bottom_left"] = area["variance"][
                f"distance_{metric}"
            ]["bottom_left"].sqrt()

            # !Calculate the error for the distances
            area["error"][f"distance_{metric}"]["top_left"] = (
                area["stdev"][f"distance_{metric}"]["top_left"] / n_sqrt
            )
            area["error"][f"distance_{metric}"]["top_right"] = (
                area["stdev"][f"distance_{metric}"]["top_right"] / n_sqrt
            )
            area["error"][f"distance_{metric}"]["bottom_right"] = (
                area["stdev"][f"distance_{metric}"]["bottom_right"] / n_sqrt
            )
            area["error"][f"distance_{metric}"]["bottom_left"] = (
                area["stdev"][f"distance_{metric}"]["bottom_left"] / n_sqrt
            )

        return area

    @classmethod
    def __calc_info_stats(cls, base_data_info: BaseInfo, data: Info) -> BaseInfo:
        """Calculate the stats for the info."""

        old_sample_size = base_data_info["sample_size"] - 1
        n_sqrt = Decimal(base_data_info["sample_size"]).sqrt()
        for metric in ["px", "mm"]:
            # !Old means
            means = {
                "area": base_data_info["stats"]["mean"][f"area_{metric}"],
                "delta": base_data_info["stats"]["mean"][f"delta_{metric}"],
            }

            # !Calculate the mean for the info
            base_data_info["stats"]["mean"][f"area_{metric}"] = cls.__calc_mean(
                base_data_info["stats"]["mean"][f"area_{metric}"],
                base_data_info["sample_size"],
                data["box"][f"area_{metric}"],
            )
            base_data_info["stats"]["mean"][f"delta_{metric}"]["x"] = cls.__calc_mean(
                base_data_info["stats"]["mean"][f"delta_{metric}"]["x"],
                base_data_info["sample_size"],
                data["box"][f"delta_{metric}"]["x"],
            )
            base_data_info["stats"]["mean"][f"delta_{metric}"]["y"] = cls.__calc_mean(
                base_data_info["stats"]["mean"][f"delta_{metric}"]["y"],
                base_data_info["sample_size"],
                data["box"][f"delta_{metric}"]["y"],
            )

            # !Calculate the variance for the info
            base_data_info["stats"]["variance"][f"area_{metric}"] = cls.__calc_variance(
                base_data_info["stats"]["variance"][f"area_{metric}"],
                means["area"],
                base_data_info["stats"]["mean"][f"area_{metric}"],
                old_sample_size,
                data["box"][f"area_{metric}"],
            )
            base_data_info["stats"]["variance"][f"delta_{metric}"]["x"] = (
                cls.__calc_variance(
                    base_data_info["stats"]["variance"][f"delta_{metric}"]["x"],
                    means["delta"]["x"],
                    base_data_info["stats"]["mean"][f"delta_{metric}"]["x"],
                    old_sample_size,
                    data["box"][f"delta_{metric}"]["x"],
                )
            )
            base_data_info["stats"]["variance"][f"delta_{metric}"]["y"] = (
                cls.__calc_variance(
                    base_data_info["stats"]["variance"][f"delta_{metric}"]["y"],
                    means["delta"]["y"],
                    base_data_info["stats"]["mean"][f"delta_{metric}"]["y"],
                    old_sample_size,
                    data["box"][f"delta_{metric}"]["y"],
                )
            )

            # !Calculate the standard deviation for the info
            base_data_info["stats"]["stdev"][f"area_{metric}"] = base_data_info[
                "stats"
            ]["variance"][f"area_{metric}"].sqrt()
            base_data_info["stats"]["stdev"][f"delta_{metric}"]["x"] = base_data_info[
                "stats"
            ]["variance"][f"delta_{metric}"]["x"].sqrt()
            base_data_info["stats"]["stdev"][f"delta_{metric}"]["y"] = base_data_info[
                "stats"
            ]["variance"][f"delta_{metric}"]["y"].sqrt()

            # !Calculate the error for the info
            base_data_info["stats"]["error"][f"area_{metric}"] = (
                base_data_info["stats"]["stdev"][f"area_{metric}"] / n_sqrt
            )
            base_data_info["stats"]["error"][f"delta_{metric}"]["x"] = (
                base_data_info["stats"]["stdev"][f"delta_{metric}"]["x"] / n_sqrt
            )
            base_data_info["stats"]["error"][f"delta_{metric}"]["y"] = (
                base_data_info["stats"]["stdev"][f"delta_{metric}"]["y"] / n_sqrt
            )

        return base_data_info
