from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .rate_limited_session import RateLimitedSession
from ..model.timestep import Timestep


class RealtimePricesClient:
    """Client for fetching realtime prices from the OSRS prices API."""

    def __init__(self, user_agent: str, retries=3):
        self.session = RateLimitedSession(max_tps=3)
        self.session.headers.update({"User-Agent": user_agent})

        retry = Retry(
            total=retries,
            backoff_factor=0.3,
            status_forcelist=list(range(500, 600)),
            allowed_methods=None,  # retry on everything
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)

    def _get_endpoint(self, item_id: str, timestep: Timestep) -> str:
        return (
            "https://prices.runescape.wiki"
            f"/api/v1/osrs/timeseries?timestep={timestep.value}&id={item_id}"
        )

    def _get_mapping_endpoint(self) -> str:
        return "https://prices.runescape.wiki/api/v1/osrs/mapping"

    def _call_endpoint(self, item_id: str, timestep: Timestep) -> Response:
        endpoint = self._get_endpoint(item_id, timestep)
        response = self.session.request("GET", endpoint)
        return response

    def _call_mapping_endpoint(self) -> Response:
        endpoint = self._get_mapping_endpoint()
        response = self.session.request("GET", endpoint)
        return response
