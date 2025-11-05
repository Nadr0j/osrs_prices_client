from dataclasses import dataclass
from .timestep import Timestep
from .interpolation_method import InterpolationMethod

@dataclass
class RealtimePricesRequest:
    """Data class representing a request for realtime prices with parameters."""
    item_ids: set[str]
    timestep: Timestep
    interpolation_method: InterpolationMethod = InterpolationMethod.NONE
