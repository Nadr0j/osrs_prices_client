import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from osrs_prices_client import (
    AverageTrueRange,
    BollingerBands,
    FeatureBuilder,
    ExponentialMovingAverage,
    ForwardLogReturn,
    ForwardVWAPDirection,
    ForwardVWAPReturn,
    LagFeature,
    LogReturn,
    MidpointPrice,
    RateOfChange,
    RollingMean,
    RollingMedian,
    RollingPriceChannel,
    RollingVolume,
    RollingVolatility,
    SimpleReturn,
    VolumeWeightedAveragePrice,
)


def test_volume_weighted_average_price_build_creates_expected_column():
    data = pd.DataFrame(
        {
            "avgHighPrice": [10.0, 20.0],
            "avgLowPrice": [8.0, 16.0],
            "highPriceVolume": [2.0, 2.0],
            "lowPriceVolume": [1.0, 1.0],
        }
    )

    builder = VolumeWeightedAveragePrice()
    result = builder.build(data)

    expected = pd.Series([9.3333333333, 18.6666666667], name="volume_weighted_average_price")
    pdt.assert_series_equal(result["volume_weighted_average_price"], expected, atol=1e-10, rtol=0)


def test_forward_vwap_return_generates_shifted_returns():
    prices = pd.DataFrame({"volume_weighted_average_price": [100.0, 110.0, 121.0, 133.1]})
    builder = ForwardVWAPReturn(horizons=[1, 2])

    result = builder.build(prices)

    expected_h1 = pd.Series([0.1, 0.1, 0.1, np.nan], name="vwap_return_fwd_1")
    expected_h2 = pd.Series([0.1, 0.1, np.nan, np.nan], name="vwap_return_fwd_2")

    pdt.assert_series_equal(result["vwap_return_fwd_1"], expected_h1, check_names=True, atol=1e-12)
    pdt.assert_series_equal(result["vwap_return_fwd_2"], expected_h2, check_names=True, atol=1e-12)


def test_forward_vwap_direction_flags_positive_returns():
    prices = pd.DataFrame({"volume_weighted_average_price": [100.0, 110.0, 121.0, 133.1]})
    builder = ForwardVWAPDirection(horizons=[1, 2])

    result = builder.build(prices)

    assert result["vwap_up_fwd_1"].dtype == "Int8"
    assert result["vwap_up_fwd_1"].tolist() == [1, 1, 1, 0]
    assert result["vwap_up_fwd_2"].tolist() == [1, 1, 0, 0]


def test_volume_weighted_average_price_metadata_exposes_requirements_and_name():
    builder = VolumeWeightedAveragePrice()

    assert builder.get_name() == "volume_weighted_average_price"
    assert builder.requires() == {"avgHighPrice", "avgLowPrice", "highPriceVolume", "lowPriceVolume"}
    assert builder.provides() == {"volume_weighted_average_price"}


def test_midpoint_price_builder_creates_expected_series():
    data = pd.DataFrame(
        {
            "avgHighPrice": [10.0, 12.0, 14.0],
            "avgLowPrice": [6.0, 8.0, 10.0],
        }
    )

    builder = MidpointPrice()
    result = builder.build(data)

    expected = pd.Series([8.0, 10.0, 12.0], name="midpoint_price")
    pdt.assert_series_equal(result["midpoint_price"], expected, check_names=True)
    assert builder.requires() == {"avgHighPrice", "avgLowPrice"}
    assert builder.provides() == {"midpoint_price"}


def test_exponential_moving_average_builder_matches_pandas_ewm():
    prices = pd.DataFrame({"midpoint_price": [10.0, 20.0, 15.0, 25.0]})
    builder = ExponentialMovingAverage(column="midpoint_price", span=2)

    result = builder.build(prices)

    expected = prices["midpoint_price"].ewm(span=2, adjust=False).mean()
    expected.name = "ema_midpoint_price_2"
    pdt.assert_series_equal(result["ema_midpoint_price_2"], expected, check_names=True)


def test_simple_return_builder_matches_arithmetic_returns():
    prices = pd.DataFrame({"midpoint_price": [10.0, 20.0, 40.0]})
    builder = SimpleReturn(column="midpoint_price", horizons=[1, 2])

    result = builder.build(prices)

    expected_h1 = prices["midpoint_price"] / prices["midpoint_price"].shift(1) - 1
    expected_h1.name = "simple_return_midpoint_price_1"
    expected_h2 = prices["midpoint_price"] / prices["midpoint_price"].shift(2) - 1
    expected_h2.name = "simple_return_midpoint_price_2"

    pdt.assert_series_equal(result["simple_return_midpoint_price_1"], expected_h1, check_names=True)
    pdt.assert_series_equal(result["simple_return_midpoint_price_2"], expected_h2, check_names=True)


def test_log_return_builder_computes_expected_values():
    prices = pd.DataFrame({"midpoint_price": [10.0, 20.0, 40.0, 80.0]})
    builder = LogReturn(column="midpoint_price", horizons=[1, 2])

    result = builder.build(prices)

    expected_h1 = np.log(prices["midpoint_price"] / prices["midpoint_price"].shift(1))
    expected_h1.name = "log_return_midpoint_price_1"
    expected_h2 = np.log(prices["midpoint_price"] / prices["midpoint_price"].shift(2))
    expected_h2.name = "log_return_midpoint_price_2"

    pdt.assert_series_equal(result["log_return_midpoint_price_1"], expected_h1, check_names=True)
    pdt.assert_series_equal(result["log_return_midpoint_price_2"], expected_h2, check_names=True)


def test_forward_log_return_builder_computes_expected_values():
    prices = pd.DataFrame({"midpoint_price": [10.0, 20.0, 40.0, 80.0]})
    builder = ForwardLogReturn(column="midpoint_price", horizons=[1, 3])

    result = builder.build(prices)

    expected_h1 = np.log(prices["midpoint_price"].shift(-1) / prices["midpoint_price"])
    expected_h1.name = "forward_log_returns_midpoint_price_1"
    expected_h3 = np.log(prices["midpoint_price"].shift(-3) / prices["midpoint_price"])
    expected_h3.name = "forward_log_returns_midpoint_price_3"

    pdt.assert_series_equal(result["forward_log_returns_midpoint_price_1"], expected_h1, check_names=True)
    pdt.assert_series_equal(result["forward_log_returns_midpoint_price_3"], expected_h3, check_names=True)


def test_rolling_volatility_builder_matches_manual_calculation():
    prices = pd.DataFrame({"midpoint_price": [10.0, 11.0, 9.0, 12.0, 15.0]})
    builder = RollingVolatility(column="midpoint_price", window=3, periods_per_year=365)

    result = builder.build(prices)

    log_returns = np.log(prices["midpoint_price"] / prices["midpoint_price"].shift(1))
    expected = log_returns.rolling(3).std(ddof=0) * np.sqrt(365)
    expected.name = "rolling_volatility_midpoint_price_3_annualized"

    pdt.assert_series_equal(result["rolling_volatility_midpoint_price_3_annualized"], expected, check_names=True)


def test_rolling_mean_and_median_builders_compute_expected_values():
    prices = pd.DataFrame({"midpoint_price": [1.0, 2.0, 3.0, 4.0]})
    mean_builder = RollingMean(column="midpoint_price", window=2, min_periods=None)
    median_builder = RollingMedian(column="midpoint_price", window=3, min_periods=2)

    assert mean_builder.get_name() == "rolling_mean_midpoint_price_2"
    assert mean_builder.requires() == {"midpoint_price"}
    assert mean_builder.provides() == {"rolling_mean_midpoint_price_2"}
    assert median_builder.get_name() == "rolling_median_midpoint_price_3"
    assert median_builder.requires() == {"midpoint_price"}
    assert median_builder.provides() == {"rolling_median_midpoint_price_3"}

    mean_result = mean_builder.build(prices)
    median_result = median_builder.build(prices)

    expected_mean = prices["midpoint_price"].rolling(2).mean()
    expected_mean.name = "rolling_mean_midpoint_price_2"
    expected_median = prices["midpoint_price"].rolling(3, min_periods=2).median()
    expected_median.name = "rolling_median_midpoint_price_3"

    pdt.assert_series_equal(mean_result["rolling_mean_midpoint_price_2"], expected_mean, check_names=True)
    pdt.assert_series_equal(median_result["rolling_median_midpoint_price_3"], expected_median, check_names=True)


def test_rolling_price_channel_tracks_extrema():
    prices = pd.DataFrame({"midpoint_price": [2.0, 5.0, 1.0, 4.0]})
    builder = RollingPriceChannel(column="midpoint_price", window=2)

    result = builder.build(prices)

    assert result["price_channel_midpoint_price_2_high"].tolist() == [2.0, 5.0, 5.0, 4.0]
    assert result["price_channel_midpoint_price_2_low"].tolist() == [2.0, 2.0, 1.0, 1.0]


def test_bollinger_bands_builder_matches_manual_calculation():
    prices = pd.DataFrame({"midpoint_price": [10.0, 10.0, 10.0, 10.0]})
    builder = BollingerBands(column="midpoint_price", window=2, std_factor=2.0)

    result = builder.build(prices)
    rolling = prices["midpoint_price"].rolling(2)
    mean = rolling.mean()
    std = rolling.std(ddof=0)

    upper_expected = mean + 2 * std
    upper_expected.name = "bollinger_midpoint_price_2_upper"
    lower_expected = mean - 2 * std
    lower_expected.name = "bollinger_midpoint_price_2_lower"
    zscore_expected = (prices["midpoint_price"] - mean) / std
    zscore_expected.name = "bollinger_midpoint_price_2_zscore"

    pdt.assert_series_equal(result["bollinger_midpoint_price_2_upper"], upper_expected, check_names=True)
    pdt.assert_series_equal(result["bollinger_midpoint_price_2_lower"], lower_expected, check_names=True)
    pdt.assert_series_equal(result["bollinger_midpoint_price_2_zscore"], zscore_expected, check_names=True)


def test_average_true_range_builder_matches_hand_calculation():
    data = pd.DataFrame(
        {
            "avgHighPrice": [12.0, 14.0, 13.0],
            "avgLowPrice": [8.0, 11.0, 10.0],
            "midpoint_price": [10.0, 12.0, 11.0],
        }
    )
    builder = AverageTrueRange(
        high_column="avgHighPrice",
        low_column="avgLowPrice",
        close_column="midpoint_price",
        window=2,
    )

    result = builder.build(data)

    high = data["avgHighPrice"]
    low = data["avgLowPrice"]
    close = data["midpoint_price"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    expected = tr.rolling(2).mean()
    expected.name = "atr_2"

    pdt.assert_series_equal(result["atr_2"], expected, check_names=True)


def test_rolling_volume_builder_adds_total_and_mean():
    data = pd.DataFrame(
        {
            "highPriceVolume": [1.0, 2.0, 3.0, 4.0],
            "lowPriceVolume": [0.5, 1.5, 2.5, 3.5],
        }
    )
    builder = RollingVolume(
        high_volume_column="highPriceVolume",
        low_volume_column="lowPriceVolume",
        window=2,
    )

    result = builder.build(data)

    total_expected = data["highPriceVolume"] + data["lowPriceVolume"]
    total_expected.name = "total_volume"
    mean_expected = total_expected.rolling(2).mean()
    mean_expected.name = "rolling_volume_2_mean"

    pdt.assert_series_equal(result["total_volume"], total_expected, check_names=True)
    pdt.assert_series_equal(result["rolling_volume_2_mean"], mean_expected, check_names=True)


def test_rate_of_change_builder_matches_formula():
    prices = pd.DataFrame({"midpoint_price": [10.0, 20.0, 40.0, 80.0]})
    builder = RateOfChange(column="midpoint_price", window=2)

    result = builder.build(prices)

    expected = prices["midpoint_price"] / prices["midpoint_price"].shift(2) - 1
    expected.name = "roc_midpoint_price_2"
    pdt.assert_series_equal(result["roc_midpoint_price_2"], expected, check_names=True)


def test_lag_feature_builder_creates_shifted_columns_with_optional_fill():
    prices = pd.DataFrame({"midpoint_price": [10.0, 20.0, 30.0, 40.0]})
    builder = LagFeature(column="midpoint_price", lags=[1, 2], fill_method=None)

    result = builder.build(prices)

    expected_lag1 = prices["midpoint_price"].shift(1)
    expected_lag1.name = "lag_midpoint_price_1"
    expected_lag2 = prices["midpoint_price"].shift(2)
    expected_lag2.name = "lag_midpoint_price_2"

    pdt.assert_series_equal(result["lag_midpoint_price_1"], expected_lag1, check_names=True)
    pdt.assert_series_equal(result["lag_midpoint_price_2"], expected_lag2, check_names=True)

    builder_ffill = LagFeature(column="midpoint_price", lags=[1], fill_method="ffill")
    result_ffill = builder_ffill.build(prices)
    assert result_ffill["lag_midpoint_price_1"].tolist() == [10.0, 10.0, 20.0, 30.0]


def test_forward_vwap_return_metadata_reflects_requested_horizons():
    builder = ForwardVWAPReturn(horizons=[2, 4])

    assert builder.get_name() == "forward_vwap_returns"
    assert builder.requires() == {"volume_weighted_average_price"}
    assert builder.provides() == {"vwap_return_fwd_2", "vwap_return_fwd_4"}


def test_forward_vwap_direction_metadata_reflects_requested_horizons():
    builder = ForwardVWAPDirection(horizons=[3])

    assert builder.get_name() == "forward_vwap_directions"
    assert builder.requires() == {"volume_weighted_average_price"}
    assert builder.provides() == {"vwap_up_fwd_3"}


def test_feature_builder_base_methods_have_no_default_behavior():
    class PassthroughBuilder(FeatureBuilder):
        def get_name(self) -> str:
            return super().get_name()

        def requires(self) -> set[str]:
            return super().requires()

        def provides(self) -> set[str]:
            return super().provides()

        def build(self, data: pd.DataFrame) -> pd.DataFrame:
            return super().build(data)

    builder = PassthroughBuilder()

    assert FeatureBuilder.get_name(builder) is None
    assert FeatureBuilder.requires(builder) is None
    assert FeatureBuilder.provides(builder) is None
    assert FeatureBuilder.build(builder, pd.DataFrame()) is None


def test_exponential_moving_average_metadata_and_validation():
    builder = ExponentialMovingAverage(column="midpoint_price", span=5)
    assert builder.get_name() == "ema_midpoint_price_5"
    assert builder.requires() == {"midpoint_price"}
    assert builder.provides() == {"ema_midpoint_price_5"}

    with pytest.raises(ValueError):
        ExponentialMovingAverage(column="midpoint_price", span=0)


def test_simple_return_metadata_and_validation():
    builder = SimpleReturn(column="midpoint_price", horizons=[1, 3])
    assert builder.get_name() == "simple_return_midpoint_price"
    assert builder.requires() == {"midpoint_price"}
    assert builder.provides() == {"simple_return_midpoint_price_1", "simple_return_midpoint_price_3"}

    with pytest.raises(ValueError):
        SimpleReturn(column="midpoint_price", horizons=[])
    with pytest.raises(ValueError):
        SimpleReturn(column="midpoint_price", horizons=[0])


def test_log_return_metadata_and_validation():
    builder = LogReturn(column="midpoint_price", horizons=[2])
    assert builder.get_name() == "log_return_midpoint_price"
    assert builder.requires() == {"midpoint_price"}
    assert builder.provides() == {"log_return_midpoint_price_2"}

    with pytest.raises(ValueError):
        LogReturn(column="midpoint_price", horizons=[])
    with pytest.raises(ValueError):
        LogReturn(column="midpoint_price", horizons=[-1])


def test_forward_log_return_metadata_and_validation():
    builder = ForwardLogReturn(column="midpoint_price", horizons=[1])
    assert builder.get_name() == "forward_log_returns_midpoint_price"
    assert builder.requires() == {"midpoint_price"}
    assert builder.provides() == {"forward_log_returns_midpoint_price_1"}

    with pytest.raises(ValueError):
        ForwardLogReturn(column="midpoint_price", horizons=[])
    with pytest.raises(ValueError):
        ForwardLogReturn(column="midpoint_price", horizons=[0])


def test_forward_vwap_builders_validate_horizons():
    with pytest.raises(ValueError):
        ForwardVWAPReturn(horizons=[])
    with pytest.raises(ValueError):
        ForwardVWAPDirection(horizons=[])


def test_rolling_volatility_metadata_and_validation():
    builder = RollingVolatility(column="midpoint_price", window=5, periods_per_year=252)
    assert builder.get_name() == "rolling_volatility_midpoint_price_5_annualized"
    assert builder.requires() == {"midpoint_price"}
    assert builder.provides() == {"rolling_volatility_midpoint_price_5_annualized"}

    with pytest.raises(ValueError):
        RollingVolatility(column="midpoint_price", window=1, periods_per_year=252)
    with pytest.raises(ValueError):
        RollingVolatility(column="midpoint_price", window=5, periods_per_year=0)


def test_rolling_mean_and_median_validate_parameters():
    with pytest.raises(ValueError):
        RollingMean(column="midpoint_price", window=0, min_periods=1)
    with pytest.raises(ValueError):
        RollingMedian(column="midpoint_price", window=0, min_periods=1)


def test_rolling_price_channel_and_rate_of_change_metadata():
    channel = RollingPriceChannel(column="midpoint_price", window=3)
    assert channel.get_name() == "price_channel_midpoint_price_3"
    assert channel.requires() == {"midpoint_price"}
    assert channel.provides() == {
        "price_channel_midpoint_price_3_high",
        "price_channel_midpoint_price_3_low",
    }
    with pytest.raises(ValueError):
        RollingPriceChannel(column="midpoint_price", window=0)

    roc = RateOfChange(column="midpoint_price", window=4)
    assert roc.get_name() == "roc_midpoint_price_4"
    assert roc.requires() == {"midpoint_price"}
    assert roc.provides() == {"roc_midpoint_price_4"}
    with pytest.raises(ValueError):
        RateOfChange(column="midpoint_price", window=0)


def test_bollinger_bands_average_true_range_and_volume_metadata():
    bands = BollingerBands(column="midpoint_price", window=5, std_factor=1.5)
    expected_base = "bollinger_midpoint_price_5"
    assert bands.get_name() == expected_base
    assert bands.requires() == {"midpoint_price"}
    assert bands.provides() == {
        f"{expected_base}_upper",
        f"{expected_base}_lower",
        f"{expected_base}_zscore",
    }
    with pytest.raises(ValueError):
        BollingerBands(column="midpoint_price", window=1, std_factor=1.0)
    with pytest.raises(ValueError):
        BollingerBands(column="midpoint_price", window=5, std_factor=0)

    atr = AverageTrueRange(
        high_column="avgHighPrice",
        low_column="avgLowPrice",
        close_column="midpoint_price",
        window=14,
    )
    assert atr.get_name() == "atr_14"
    assert atr.requires() == {"avgHighPrice", "avgLowPrice", "midpoint_price"}
    assert atr.provides() == {"atr_14"}
    with pytest.raises(ValueError):
        AverageTrueRange(
            high_column="avgHighPrice",
            low_column="avgLowPrice",
            close_column="midpoint_price",
            window=0,
        )

    volume = RollingVolume(
        high_volume_column="highPriceVolume",
        low_volume_column="lowPriceVolume",
        window=3,
    )
    assert volume.get_name() == "rolling_volume_3"
    assert volume.requires() == {"highPriceVolume", "lowPriceVolume"}
    assert volume.provides() == {"total_volume", "rolling_volume_3_mean"}
    with pytest.raises(ValueError):
        RollingVolume(
            high_volume_column="highPriceVolume",
            low_volume_column="lowPriceVolume",
            window=0,
        )


def test_lag_feature_metadata_and_validation():
    builder = LagFeature(column="midpoint_price", lags=[1, 2], fill_method=None)
    assert builder.get_name() == "lag_midpoint_price"
    assert builder.requires() == {"midpoint_price"}
    assert builder.provides() == {"lag_midpoint_price_1", "lag_midpoint_price_2"}

    with pytest.raises(ValueError):
        LagFeature(column="midpoint_price", lags=[], fill_method=None)
    with pytest.raises(ValueError):
        LagFeature(column="midpoint_price", lags=[-1], fill_method=None)
    with pytest.raises(ValueError):
        LagFeature(column="midpoint_price", lags=[1], fill_method="invalid")
