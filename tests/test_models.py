from osrs_prices_client import (
    InterpolationFill,
    InterpolationMethod,
    RealtimePricesRequest,
    Timestep,
)


def test_realtime_prices_request_defaults_to_no_interpolation():
    request = RealtimePricesRequest(item_ids={"100"}, timestep=Timestep.ONE_DAY)

    assert request.interpolation_method is InterpolationMethod.NONE
    assert request.interpolation_fill is InterpolationFill.FORWARD_FILL


def test_timestep_enum_has_expected_value():
    assert Timestep.ONE_DAY.value == "24h"
