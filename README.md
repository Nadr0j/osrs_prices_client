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
from osrs_prices_client import (
    RealtimePricesClient,
    RealtimePricesThickClient,
    RealtimePricesRequest,
    Timestep,
    InterpolationMethod,
    VolumeWeightedAveragePrice,
    ForwardVWAPReturn,
    FeatureBuilderOrchestrator,
)

client = RealtimePricesClient(user_agent="my-osrs-app/0.1")
thick = RealtimePricesThickClient(client)

request = RealtimePricesRequest(
    item_ids={"4151", "11840"},
    timestep=Timestep.ONE_DAY,
    interpolation_method=InterpolationMethod.LINEAR,
)
prices = thick.get_prices(request)

builders = [
    VolumeWeightedAveragePrice(),      # adds volume_weighted_average_price
    ForwardVWAPReturn(horizons=[1, 3]) # adds vwap_return_fwd_1 and vwap_return_fwd_3
]
features = FeatureBuilderOrchestrator.build_features(prices, builders)
print(features.columns)
```
The resulting dataframe keeps each item in a MultiIndex column (`item_id`, `feature_name`). Any feature claimed by a builder is appended to the item’s columns, so downstream consumers can select features per item or flatten the index as needed.

## Roll Your Own Feature Builder
Creating a new feature is as simple as subclassing `FeatureBuilder`, declaring the columns you require, and returning a dataframe with the new columns. Here’s a playful example that computes a z-scored VWAP to highlight unusual price moves:

```python
from dataclasses import dataclass
import pandas as pd
from osrs_prices_client import FeatureBuilder

@dataclass
class VWAPZScore(FeatureBuilder):
    window: int = 14

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
    VolumeWeightedAveragePrice(),
    VWAPZScore(window=14),
]
features = FeatureBuilderOrchestrator.build_features(prices, builders)
```
Mix and match as many builders as you like—the orchestrator raises a helpful error if any requirements are unsatisfied, preventing silent failures.

## Bundled Feature Builders
- `VolumeWeightedAveragePrice`: aggregates wiki high/low prices and volumes into a single VWAP series.
- `ForwardVWAPReturn`: generates forward-looking percentage returns for configurable horizons.
- `ForwardVWAPDirection`: produces boolean targets indicating whether returns are positive over each horizon.

Bring your own builders to extend this list with alpha signals, risk metrics, or anything else your workflow needs.

## License
Released under the MIT License. See `LICENSE` for details.
