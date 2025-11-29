from dataclasses import dataclass
from .timestep import Timestep
from .interpolation_method import InterpolationFill, InterpolationMethod


@dataclass
class RealtimePricesRequest:
    """Data class representing a request for realtime prices with parameters."""

    item_ids: set[str]
    timestep: Timestep
    interpolation_method: InterpolationMethod = InterpolationMethod.NONE
    interpolation_fill: InterpolationFill = InterpolationFill.FORWARD_FILL
