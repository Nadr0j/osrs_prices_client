import pandas as pd
from ..model.feature_builder import FeatureBuilder


class ForwardVWAPDirection(FeatureBuilder):
    """Boolean targets: 1 if forward return > 0, else 0."""

    def __init__(self, horizons: list[int]):
        if not horizons:
            raise ValueError("horizons must be provided")
        self.horizons = horizons

    def get_name(self) -> str:
        return "forward_vwap_directions"

    def requires(self) -> set[str]:
        return {"volume_weighted_average_price"}

    def provides(self) -> set[str]:
        return {f"vwap_up_fwd_{h}" for h in self.horizons}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        price = df["volume_weighted_average_price"]
        ret = price.pct_change()
        for h in self.horizons:
            fwd_ret = ret.shift(-h)
            df[f"vwap_up_fwd_{h}"] = (fwd_ret > 0).astype("Int8")  # or bool
        return df
