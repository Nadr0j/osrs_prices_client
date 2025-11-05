from unittest.mock import MagicMock

import pandas as pd
import pytest

from osrs_prices_client import (
    InterpolationMethod,
    RealtimePricesClient,
    RealtimePricesRequest,
    RealtimePricesThickClient,
    Timestep,
)


def _response_with_data(data: list[dict]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"data": data}
    return response


def test_thick_client_parses_and_interpolates_responses():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_endpoint.side_effect = [
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
                {"timestamp": 2, "avgHighPrice": 110},
                {"timestamp": 3, "avgHighPrice": 120},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 200},
                {"timestamp": 3, "avgHighPrice": 220},
            ]
        ),
    ]

    thick_client = RealtimePricesThickClient(realtime_client)
    request = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.LINEAR,
    )

    result = thick_client.get_prices(request)

    assert isinstance(result, pd.DataFrame)
    assert set(result.index) == {1, 2, 3}
    assert ("100", "avgHighPrice") in result.columns
    assert ("200", "avgHighPrice") in result.columns
    assert result.loc[2, ("200", "avgHighPrice")] == pytest.approx(210.0)

    realtime_client._call_endpoint.assert_any_call("100", Timestep.ONE_DAY)
    realtime_client._call_endpoint.assert_any_call("200", Timestep.ONE_DAY)
    assert realtime_client._call_endpoint.call_count == 2


def test_thick_client_keeps_missing_values_without_interpolation():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_endpoint.side_effect = [
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
                {"timestamp": 3, "avgHighPrice": 120},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 200},
                {"timestamp": 2, "avgHighPrice": 210},
                {"timestamp": 3, "avgHighPrice": 220},
            ]
        ),
    ]

    thick_client = RealtimePricesThickClient(realtime_client)
    request = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    result = thick_client.get_prices(request)

    assert set(result.index) == {1, 2, 3}
    assert pd.isna(result.loc[2, ("100", "avgHighPrice")])
    assert result.loc[2, ("200", "avgHighPrice")] == 210
