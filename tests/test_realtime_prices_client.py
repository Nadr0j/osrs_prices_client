from unittest.mock import MagicMock

import pytest
from requests.adapters import HTTPAdapter

from osrs_prices_client import RealtimePricesClient, Timestep


def test_realtime_prices_client_initializes_session_with_retry():
    client = RealtimePricesClient(user_agent="test-agent", retries=5)

    assert client.session.headers["User-Agent"] == "test-agent"

    adapter = client.session.adapters["https://"]
    assert isinstance(adapter, HTTPAdapter)
    assert adapter.max_retries.total == 5
    assert adapter.max_retries.backoff_factor == pytest.approx(0.3)
    assert adapter.max_retries.allowed_methods is None


def test_realtime_prices_client_get_endpoint():
    client = RealtimePricesClient(user_agent="agent")

    endpoint = client._get_endpoint("4151", Timestep.ONE_DAY)

    assert endpoint == "https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=24h&id=4151"


def test_realtime_prices_client_call_endpoint_uses_session():
    client = RealtimePricesClient(user_agent="agent")
    client.session.request = MagicMock(return_value="response")

    response = client._call_endpoint("4151", Timestep.ONE_DAY)

    expected_endpoint = "https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=24h&id=4151"
    client.session.request.assert_called_once_with("GET", expected_endpoint)
    assert response == "response"
