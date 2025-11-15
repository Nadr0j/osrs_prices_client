# pylint: disable=duplicate-code

from unittest.mock import MagicMock, patch

import pytest
import requests

from osrs_prices_client import clients
from osrs_prices_client.client import rate_limited_session as rate_limited_session_module


def test_rate_limited_session_respects_min_interval(monkeypatch):
    session = clients.RateLimitedSession(max_tps=2)  # 0.5 seconds between calls

    time_values = iter([0.0, 0.5, 1.0, 1.6])
    sleep_calls: list[float] = []

    def fake_time():
        return next(time_values)

    def fake_sleep(duration: float):
        sleep_calls.append(duration)

    monkeypatch.setattr(rate_limited_session_module.time, "time", fake_time)
    monkeypatch.setattr(rate_limited_session_module.time, "sleep", fake_sleep)

    with patch.object(requests.Session, "request", return_value=MagicMock()) as mock_request:
        session.request("GET", "https://example.com/first")
        session.request("GET", "https://example.com/second")

    assert mock_request.call_count == 2
    assert sleep_calls == [pytest.approx(0.5)]
    # pylint: disable-next=protected-access
    assert session._last == pytest.approx(1.6)
