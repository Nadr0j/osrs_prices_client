"""Built-in feature builders made available by the package."""

from .average_true_range import AverageTrueRange
from .bollinger_bands import BollingerBands
from .exponential_moving_average import ExponentialMovingAverage
from .forward_log_return import ForwardLogReturn
from .forward_vwap_direction import ForwardVWAPDirection
from .forward_vwap_return import ForwardVWAPReturn
from .lag_feature import LagFeature
from .log_return import LogReturn
from .midpoint_price import MidpointPrice
from .rate_of_change import RateOfChange
from .rolling_mean import RollingMean
from .rolling_median import RollingMedian
from .rolling_price_channel import RollingPriceChannel
from .rolling_volume import RollingVolume
from .rolling_volatility import RollingVolatility
from .simple_return import SimpleReturn
from .vwap import VolumeWeightedAveragePrice

# Ordered tuple of all bundled feature builder classes for easy introspection.
BUILT_IN_BUILDERS = (
    AverageTrueRange,
    BollingerBands,
    ExponentialMovingAverage,
    ForwardLogReturn,
    ForwardVWAPDirection,
    ForwardVWAPReturn,
    LagFeature,
    LogReturn,
    MidpointPrice,
    RateOfChange,
    RollingMean,
    RollingMedian,
    RollingPriceChannel,
    RollingVolume,
    RollingVolatility,
    SimpleReturn,
    VolumeWeightedAveragePrice,
)

__all__ = [
    "AverageTrueRange",
    "BollingerBands",
    "ExponentialMovingAverage",
    "ForwardLogReturn",
    "ForwardVWAPDirection",
    "ForwardVWAPReturn",
    "LagFeature",
    "LogReturn",
    "MidpointPrice",
    "RateOfChange",
    "RollingMean",
    "RollingMedian",
    "RollingPriceChannel",
    "RollingVolume",
    "RollingVolatility",
    "SimpleReturn",
    "VolumeWeightedAveragePrice",
    "BUILT_IN_BUILDERS",
]
