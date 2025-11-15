from enum import Enum


class InterpolationMethod(Enum):
    """Enumeration of supported interpolation methods for price data."""

    LINEAR = "linear"
    NONE = "none"
