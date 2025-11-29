from enum import Enum


class InterpolationMethod(Enum):
    """Enumeration of supported interpolation methods for price data."""

    LINEAR = "linear"
    NONE = "none"


class InterpolationFill(Enum):
    """Determines where interpolation should be applied within a series."""

    ALL = "all"
    BACKFILL = "backfill"
    FORWARD_FILL = "forward_fill"
    GAPS_ONLY = "gaps_only"
