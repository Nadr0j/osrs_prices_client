# OSRS Prices Client

A lightweight Python toolkit for fetching Old School RuneScape price history and layering feature-engineered signals on top of it. Think of it as a way to go from raw wiki prices to model-ready dataframes in just a few lines of code.

## Highlights
- **Streaming price data**: rate-limited HTTP client keeps you within RuneScape wiki guidelines and returns tidy pandas `DataFrame`s.
- **Feature pipelines**: plug-and-play feature builders (VWAP, forward returns, directional targets) with automatic dependency resolution.
- **Extensible design**: build your own `FeatureBuilder` subclasses and let the orchestrator weave them into the pipeline alongside bundled features.

## Installation
```bash
pip install osrs-prices-client
```

## Fetch Prices + Build Features
```python
import osrs_prices_client as opc

client = opc.RealtimePricesClient(user_agent="my-osrs-app/0.1")
thick = opc.RealtimePricesThickClient(client)

request = opc.models.RealtimePricesRequest(
    item_ids={"2", "4152"},
    timestep=opc.models.Timestep.ONE_DAY,
    interpolation_method=opc.models.InterpolationMethod.LINEAR,
)
prices = thick.get_prices(request)

builders = [
    opc.features.MidpointPrice(),                         # adds midpoint_price
    opc.features.ExponentialMovingAverage(
        column="midpoint_price",
        span=5,
    ),                                                    # adds ema_midpoint_price_5
]
feature_frame = opc.orchestration.FeatureBuilderOrchestrator.build_features(prices, builders)
print(feature_frame.columns)
```
The resulting dataframe keeps each item in a MultiIndex column (`item_id`, `feature_name`). Any feature claimed by a builder is appended to the item’s columns, so downstream consumers can select features per item or flatten the index as needed. Seeing the difference is as simple as printing the column index before and after:

```text
>>> prices.columns
MultiIndex(
  [('4152', 'avgHighPrice'), ('4152', 'avgLowPrice'),
   ('4152', 'highPriceVolume'), ('4152', 'lowPriceVolume'),
   ('2', 'avgHighPrice'), ('2', 'avgLowPrice'),
   ('2', 'highPriceVolume'), ('2', 'lowPriceVolume')]
)

>>> feature_frame.columns
MultiIndex(
  [('4152', 'avgHighPrice'), ('4152', 'avgLowPrice'),
   ('4152', 'highPriceVolume'), ('4152', 'lowPriceVolume'),
   ('4152', 'midpoint_price'), ('4152', 'ema_midpoint_price_5'),
   ('2', 'avgHighPrice'), ('2', 'avgLowPrice'),
   ('2', 'highPriceVolume'), ('2', 'lowPriceVolume'),
   ('2', 'midpoint_price'), ('2', 'ema_midpoint_price_5')]
)
```
Notice how each item retains the raw wiki fields while the engineered signals are appended under the same item key. That’s the pattern every feature builder follows.

## Develop Your Own Feature Builders
Every custom feature must subclass `opc.FeatureBuilder` and implements four methods:
- `get_name(self) -> str`: returns a stable identifier used for logging and column naming.
- `requires(self) -> set[str]`: lists the base/derived columns that must exist before `build` runs.
- `provides(self) -> set[str]`: declares the column names your builder will add; keeps dependency resolution predictable.
- `build(self, data: pd.DataFrame) -> pd.DataFrame`: copies or mutates the dataframe and returns it with the new columns attached.

Accept any tunable parameters in `__init__` so the builder remains flexible.
Here’s an example that puts those hooks into action by computing a z-scored VWAP:

```python
import pandas as pd
import osrs_prices_client as opc


class VWAPZScore(opc.FeatureBuilder):
    def __init__(self, window: int):
        self.window = window

    def get_name(self) -> str:
        return f"vwap_zscore_{self.window}"

    def requires(self) -> set[str]:
        return {"volume_weighted_average_price"}

    def provides(self) -> set[str]:
        return {self.get_name()}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        vwap = df["volume_weighted_average_price"]
        rolling = vwap.rolling(self.window)
        df[self.get_name()] = (vwap - rolling.mean()) / rolling.std(ddof=0)
        return df
```
Add the new builder to your list and the orchestrator will ensure dependencies (like `volume_weighted_average_price`) are built first:

```python
builders = [
    opc.features.VolumeWeightedAveragePrice(),
    VWAPZScore(window=14),
]
feature_frame = opc.orchestration.FeatureBuilderOrchestrator.build_features(prices, builders)
```
Mix and match as many builders as you like—the orchestrator raises a helpful error if any requirements are unsatisfied, preventing silent failures.

## Bundled Feature Builders
The library ships with a full toolbox so you can mix levels, momentum, volatility, and targets without writing boilerplate:
- **Price levels & smoothing**: `MidpointPrice`, `RollingMean`, `RollingMedian`, `ExponentialMovingAverage`
- **Returns & momentum**: `SimpleReturn`, `LogReturn`, `RateOfChange`, `ForwardLogReturn`, `ForwardVWAPReturn`
- **Targets & direction**: `ForwardVWAPDirection` emits Int8 targets for up/down moves
- **Bands & volatility**: `BollingerBands`, `RollingVolatility`, `RollingPriceChannel`, `AverageTrueRange`
- **Volume & price-volume blends**: `VolumeWeightedAveragePrice`, `RollingVolume`, `LagFeature`

Instantiate any of these via `opc.features.<BuilderName>` and call `opc.features.BUILT_IN_BUILDERS` when you need the definitive list. When you outgrow the defaults, drop in your own `opc.FeatureBuilder` subclasses.

## Development
Install the optional dev dependencies and format/lint before sending changes upstream:

```bash
pip install -e .[dev]
black src tests
pylint src tests
```

The lint configuration lives in `.pylintrc` and already adds `src/` to `PYTHONPATH`, so imports should resolve without extra flags. Formatting is handled by Black with a 100-column limit to line up with pylint—run it before committing so diffs stay minimal, then follow up with pylint to catch logic/style issues that formatters can’t fix.

## License
Released under the MIT License. See `LICENSE` for details.
