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
from osrs_prices_client.exceptions import InvalidItemIdError


def _response_with_data(data: list[dict]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"data": data}
    return response


def _mapping_response(ids: list[int]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = [{"id": item_id} for item_id in ids]
    return response


def test_thick_client_parses_and_interpolates_responses():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200])
    # pylint: disable-next=protected-access
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

    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.assert_any_call("100", Timestep.ONE_DAY)
    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.assert_any_call("200", Timestep.ONE_DAY)
    # pylint: disable-next=protected-access
    assert realtime_client._call_endpoint.call_count == 2


def test_thick_client_keeps_missing_values_without_interpolation():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200])
    # pylint: disable-next=protected-access
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


def test_thick_client_caches_per_item_frames_by_default():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200])

    responses = {
        "100": _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
                {"timestamp": 2, "avgHighPrice": 110},
            ]
        ),
        "200": _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 200},
                {"timestamp": 2, "avgHighPrice": 210},
            ]
        ),
    }

    def _call_endpoint_side_effect(item_id, timestep):  # pylint: disable=unused-argument
        return responses[item_id]

    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.side_effect = _call_endpoint_side_effect

    thick_client = RealtimePricesThickClient(realtime_client)
    request = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    first = thick_client.get_prices(request)
    second = thick_client.get_prices(request)

    pd.testing.assert_frame_equal(first, second)

    # pylint: disable-next=protected-access
    assert realtime_client._call_endpoint.call_count == 2


def test_thick_client_can_disable_cache():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200])
    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.side_effect = [
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 200},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 101},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 201},
            ]
        ),
    ]

    thick_client = RealtimePricesThickClient(realtime_client, cache_enabled=False)
    request = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    first = thick_client.get_prices(request)
    second = thick_client.get_prices(request)

    assert not first.equals(second)

    # pylint: disable-next=protected-access
    assert realtime_client._call_endpoint.call_count == 4


def test_thick_client_clear_cache_triggers_refetch():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200])
    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.side_effect = [
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 101},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 101},
            ]
        ),
    ]

    thick_client = RealtimePricesThickClient(realtime_client)
    request = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    thick_client.get_prices(request)
    thick_client.clear_cache()
    thick_client.get_prices(request)

    # pylint: disable-next=protected-access
    assert realtime_client._call_endpoint.call_count == 4


def test_thick_client_reuses_cached_items_when_requests_overlap():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200, 300])
    call_log: list[tuple[str, Timestep]] = []

    def _call_endpoint_side_effect(item_id, timestep):
        call_log.append((item_id, timestep))
        return _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": int(item_id)},
            ]
        )

    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.side_effect = _call_endpoint_side_effect

    thick_client = RealtimePricesThickClient(realtime_client)

    request_one = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )
    request_two = RealtimePricesRequest(
        item_ids=("100", "300"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    first = thick_client.get_prices(request_one)
    second = thick_client.get_prices(request_two)

    assert ("100", "avgHighPrice") in first.columns
    assert ("200", "avgHighPrice") in first.columns
    assert ("300", "avgHighPrice") in second.columns

    assert call_log == [
        ("100", Timestep.ONE_DAY),
        ("200", Timestep.ONE_DAY),
        ("300", Timestep.ONE_DAY),
    ]


def test_thick_client_cache_preserves_raw_frames_for_future_interpolation_modes():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200])
    responses = {
        "100": _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
                {"timestamp": 3, "avgHighPrice": 120},
            ]
        ),
        "200": _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 50},
                {"timestamp": 2, "avgHighPrice": 55},
                {"timestamp": 3, "avgHighPrice": 60},
            ]
        ),
    }

    def _call_endpoint_side_effect(item_id, timestep):  # pylint: disable=unused-argument
        return responses[item_id]

    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.side_effect = _call_endpoint_side_effect

    thick_client = RealtimePricesThickClient(realtime_client)

    request_linear = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.LINEAR,
    )
    request_none = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    interpolated = thick_client.get_prices(request_linear)
    assert not pd.isna(interpolated.loc[2, ("100", "avgHighPrice")])

    raw = thick_client.get_prices(request_none)
    assert pd.isna(raw.loc[2, ("100", "avgHighPrice")])

    # pylint: disable-next=protected-access
    assert realtime_client._call_endpoint.call_count == 2


def test_thick_client_validates_item_ids_against_mapping():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([2, 4151])

    thick_client = RealtimePricesThickClient(realtime_client)
    request = RealtimePricesRequest(
        item_ids=("2", "3", "4151"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    with pytest.raises(InvalidItemIdError) as exc:
        thick_client.get_prices(request)

    assert exc.value.invalid_item_ids == ("3",)
    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.assert_not_called()


def test_thick_client_caches_mapping_lookup():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200, 300])

    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.side_effect = [
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 100},
            ]
        ),
    ]

    thick_client = RealtimePricesThickClient(realtime_client)
    request = RealtimePricesRequest(
        item_ids=("100",),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    thick_client.get_prices(request)
    thick_client.get_prices(request)

    # pylint: disable-next=protected-access
    assert realtime_client._call_mapping_endpoint.call_count == 1


def test_thick_client_skips_items_with_missing_timestamp_column():
    realtime_client = MagicMock(spec=RealtimePricesClient)
    realtime_client._call_mapping_endpoint.return_value = _mapping_response([100, 200])
    # First item returns data without a timestamp; second item is valid
    # pylint: disable-next=protected-access
    realtime_client._call_endpoint.side_effect = [
        _response_with_data(
            [
                {"avgHighPrice": 100},
            ]
        ),
        _response_with_data(
            [
                {"timestamp": 1, "avgHighPrice": 200},
            ]
        ),
    ]

    thick_client = RealtimePricesThickClient(realtime_client)
    request = RealtimePricesRequest(
        item_ids=("100", "200"),
        timestep=Timestep.ONE_DAY,
        interpolation_method=InterpolationMethod.NONE,
    )

    with pytest.warns(RuntimeWarning):
        result = thick_client.get_prices(request)

    assert ("100", "avgHighPrice") not in result.columns
    assert ("200", "avgHighPrice") in result.columns
    assert set(result.index) == {1}
