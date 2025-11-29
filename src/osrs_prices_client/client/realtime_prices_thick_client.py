from functools import lru_cache
from typing import Iterable
import warnings

import pandas as pd
from requests import Response

from .realtime_prices_client import RealtimePricesClient
from ..exceptions import InvalidItemIdError
from ..model.realtime_prices_request import RealtimePricesRequest
from ..model.timestep import Timestep
from ..model.interpolation_method import InterpolationFill, InterpolationMethod


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
        self._known_item_ids: set[str] | None = None

    def _parse_response(self, item_id: str, response: Response) -> pd.DataFrame:
        payload = response.json().get("data", [])
        if not payload:
            warnings.warn(
                f"Realtime prices response for item {item_id} contained no data; skipping item.",
                RuntimeWarning,
            )
            return pd.DataFrame(index=pd.Index([], name="timestamp"))

        df = pd.DataFrame(payload)
        if "timestamp" not in df.columns:
            warnings.warn(
                (
                    f"Realtime prices response for item {item_id} missing 'timestamp' column; "
                    "skipping item."
                ),
                RuntimeWarning,
            )
            return pd.DataFrame(index=pd.Index([], name="timestamp"))

        df = df.set_index("timestamp")
        df.columns = pd.MultiIndex.from_product([[item_id], df.columns])
        return df

    def _parse_mapping_response(self, response: Response) -> set[str]:
        payload = response.json()
        return {str(entry["id"]) for entry in payload if "id" in entry}

    def _request(self, item_id: str, timestep: Timestep) -> Response:
        # Internal collaboration with RealtimePricesClient
        # pylint: disable-next=protected-access
        return self.realtime_prices_client._call_endpoint(item_id, timestep)

    def _request_item_mapping(self) -> Response:
        # Internal collaboration with RealtimePricesClient
        # pylint: disable-next=protected-access
        return self.realtime_prices_client._call_mapping_endpoint()

    def _fetch_item_frame_uncached(self, item_id: str, timestep: Timestep) -> pd.DataFrame:
        return self._parse_response(item_id, self._request(item_id, timestep))

    def clear_cache(self) -> None:
        """Clears the cached per-item frames."""
        self._cached_fetch_item_frame.cache_clear()

    def _get_known_item_ids(self) -> set[str]:
        if self._known_item_ids is None:
            mapping_response = self._request_item_mapping()
            self._known_item_ids = self._parse_mapping_response(mapping_response)
        return self._known_item_ids

    def _validate_item_ids(self, item_ids: Iterable[str]) -> None:
        normalized_item_ids = {str(item_id) for item_id in item_ids}
        known_item_ids = self._get_known_item_ids()
        invalid_ids = normalized_item_ids.difference(known_item_ids)
        if invalid_ids:
            raise InvalidItemIdError(invalid_ids)

    def _fetch_item_frame(self, item_id: str, timestep: Timestep) -> pd.DataFrame:
        if not self._cache_enabled:
            return self._fetch_item_frame_uncached(item_id, timestep)
        return self._cached_fetch_item_frame(item_id, timestep)

    def get_prices(self, request: RealtimePricesRequest) -> pd.DataFrame:
        self._validate_item_ids(request.item_ids)
        dfs = [self._fetch_item_frame(item_id, request.timestep) for item_id in request.item_ids]
        concatenated_df = pd.concat(dfs, axis=1, join="outer").sort_index()

        if request.interpolation_method != InterpolationMethod.NONE:
            concatenated_df = self._interpolate(concatenated_df, request)

        return concatenated_df

    def _interpolate(self, df: pd.DataFrame, request: RealtimePricesRequest) -> pd.DataFrame:
        method_kwargs: dict[str, str] = {"method": request.interpolation_method.value}

        if request.interpolation_fill is InterpolationFill.GAPS_ONLY:
            method_kwargs["limit_area"] = "inside"
        elif request.interpolation_fill is InterpolationFill.FORWARD_FILL:
            method_kwargs["limit_direction"] = "forward"
        elif request.interpolation_fill is InterpolationFill.BACKFILL:
            method_kwargs["limit_direction"] = "backward"
        elif request.interpolation_fill is InterpolationFill.ALL:
            method_kwargs["limit_direction"] = "both"

        return df.interpolate(**method_kwargs)
