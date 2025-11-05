import pandas as pd
from ..model.feature_builder import FeatureBuilder

class ForwardVWAPReturn(FeatureBuilder):
    """Targets: r_{t+1}, r_{t+2}, ..."""
    def __init__(self, horizons: list[int]):
        if not horizons:
            raise ValueError("horizons must be provided")
        self.horizons = horizons

    def get_name(self) -> str:
        return "forward_vwap_returns"

    def requires(self) -> set[str]:
        return {"volume_weighted_average_price"}

    def provides(self) -> set[str]:
        return {f"vwap_return_fwd_{h}" for h in self.horizons}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        price = df["volume_weighted_average_price"]
        ret = price.pct_change()
        for h in self.horizons:
            df[f"vwap_return_fwd_{h}"] = ret.shift(-h)
        return df
