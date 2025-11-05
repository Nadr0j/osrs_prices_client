from unittest.mock import MagicMock, patch

import pytest
import requests

from osrs_prices_client import RateLimitedSession
from osrs_prices_client.client import rate_limited_session as rate_limited_session_module


def test_rate_limited_session_respects_min_interval(monkeypatch):
    session = RateLimitedSession(max_tps=2)  # 0.5 seconds between calls

    time_values = iter([0.0, 0.5, 1.0, 1.6])
    sleep_calls: list[float] = []

    monkeypatch.setattr(rate_limited_session_module.time, "time", lambda: next(time_values))
    monkeypatch.setattr(rate_limited_session_module.time, "sleep", lambda duration: sleep_calls.append(duration))

    with patch.object(requests.Session, "request", return_value=MagicMock()) as mock_request:
        session.request("GET", "https://example.com/first")
        session.request("GET", "https://example.com/second")

    assert mock_request.call_count == 2
    assert sleep_calls == [pytest.approx(0.5)]
    assert session._last == pytest.approx(1.6)
