from decimal import Decimal
from typing import Literal, TypedDict


class BoxInfo(TypedDict):
    """Type for the box info in the JSON file."""

    top_left: dict[Literal["x", "y"], int]
    top_right: dict[Literal["x", "y"], int]
    bottom_right: dict[Literal["x", "y"], int]
    bottom_left: dict[Literal["x", "y"], int]
    delta_mm: dict[Literal["x", "y"], Decimal]
    delta_px: dict[Literal["x", "y"], Decimal]
    area_mm: Decimal
    area_px: Decimal


class Info(TypedDict):
    """Type for the info in the JSON file."""

    box: BoxInfo
    mm_to_px: Decimal
    mm_to_px_squared: Decimal
    total_areas: int


class Area(TypedDict):
    """Type for the area in the JSON file."""

    id: int
    area_mm: Decimal
    area_px: int
    distance_px: dict[
        Literal["top_left", "top_right", "bottom_right", "bottom_left"], Decimal
    ]
    distance_mm: dict[
        Literal["top_left", "top_right", "bottom_right", "bottom_left"], Decimal
    ]


class NewData(TypedDict):
    """Type for the data in the JSON file."""

    info: Info
    areas: list[Area]


class InfoStats(TypedDict):
    """Type for the stats in the info in the training file."""

    area_mm: Decimal
    area_px: Decimal
    delta_mm: dict[Literal["x", "y"], Decimal]
    delta_px: dict[Literal["x", "y"], Decimal]


class BaseInfo(TypedDict):
    """Type for the info in the training file."""

    stats: dict[Literal["mean", "variance", "stdev", "error"], InfoStats]
    total_areas: int
    mm_to_px: Decimal
    mm_to_px_squared: Decimal
    sample_size: int


class BaseStatsContent(TypedDict):
    """Type for the content of each stat in the training file."""

    area_mm: Decimal
    area_px: Decimal
    distance_px: dict[
        Literal["top_left", "top_right", "bottom_right", "bottom_left"], Decimal
    ]
    distance_mm: dict[
        Literal["top_left", "top_right", "bottom_right", "bottom_left"], Decimal
    ]


class BaseArea(TypedDict):
    """Type for the area in the training file."""

    id: int
    failed: dict[Literal["area", "center", "both", "unexistent"], int]
    mean: BaseStatsContent
    variance: BaseStatsContent
    stdev: BaseStatsContent
    error: BaseStatsContent


class BaseData(TypedDict):
    """Type for the data in the training file."""

    info: BaseInfo
    areas: list[BaseArea]


class ErrorAreas(TypedDict):
    """Type for the area in the errors file."""

    id: int
    kind: Literal["area", "center", "both", "unexistent", "unexpected"]
    correct_center_mm: dict[Literal["x", "y"], Decimal]
    error_center_mm: dict[Literal["x", "y"], Decimal]
    correct_center_px: dict[Literal["x", "y"], int]
    error_center_px: dict[Literal["x", "y"], int]
    correct_area_px: Decimal
    error_area_px: Decimal
    correct_area_mm: Decimal
    error_area_mm: Decimal


class ErrorInfo(TypedDict):
    """Type for the info in the errors file."""

    rotate_correction: list[
        Literal["top_left", "top_right", "bottom_right", "bottom_left"]
    ]
    template_total_areas: int
    constants_correct: dict[Literal["mm_to_px", "mm_to_px_squared"], bool]
    sample_size: int


class Errors(TypedDict):
    """Type for the errors in the JSON file."""

    info: ErrorInfo
    is_total_areas_correct: bool
    areas: list[ErrorAreas] | None
    box: dict[Literal["correct_area_mm", "error_area_mm"], Decimal] | None
