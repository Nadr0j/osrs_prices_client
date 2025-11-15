from functools import lru_cache

import pandas as pd
from requests import Response

from .realtime_prices_client import RealtimePricesClient
from ..model.realtime_prices_request import RealtimePricesRequest
from ..model.timestep import Timestep
from ..model.interpolation_method import InterpolationMethod


class RealtimePricesThickClient:
    """Provides additional functionality around RealtimePricesClient methods"""

    def __init__(
        self,
        realtime_prices_client: RealtimePricesClient,
        *,
        cache_enabled: bool = True,
    ):
        self.realtime_prices_client = realtime_prices_client
        self._cache_enabled = cache_enabled
        self._cached_fetch_item_frame = lru_cache(maxsize=None)(self._fetch_item_frame_uncached)

    def _parse_response(self, item_id: str, response: Response) -> pd.DataFrame:
        df = pd.DataFrame(response.json()["data"])
        df = df.set_index("timestamp")
        df.columns = pd.MultiIndex.from_product([[item_id], df.columns])
        return df

    def _request(self, item_id: str, timestep: Timestep) -> Response:
        # Internal collaboration with RealtimePricesClient
        # pylint: disable-next=protected-access
        return self.realtime_prices_client._call_endpoint(item_id, timestep)

    def _fetch_item_frame_uncached(self, item_id: str, timestep: Timestep) -> pd.DataFrame:
        return self._parse_response(item_id, self._request(item_id, timestep))

    def clear_cache(self) -> None:
        """Clears the cached per-item frames."""
        self._cached_fetch_item_frame.cache_clear()

    def _fetch_item_frame(self, item_id: str, timestep: Timestep) -> pd.DataFrame:
        if not self._cache_enabled:
            return self._fetch_item_frame_uncached(item_id, timestep)
        return self._cached_fetch_item_frame(item_id, timestep)

    def get_prices(self, request: RealtimePricesRequest) -> pd.DataFrame:
        dfs = [self._fetch_item_frame(item_id, request.timestep) for item_id in request.item_ids]
        concatenated_df = pd.concat(dfs, axis=1, join="outer")

        if request.interpolation_method == InterpolationMethod.LINEAR:
            concatenated_df = concatenated_df.interpolate(method="linear")

        return concatenated_df
