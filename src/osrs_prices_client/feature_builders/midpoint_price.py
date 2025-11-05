import pandas as pd

from ..model.feature_builder import FeatureBuilder


class MidpointPrice(FeatureBuilder):
    """Computes midpoint price from the wiki avg high/low prices."""

    def get_name(self) -> str:
        return "midpoint_price"

    def requires(self) -> set[str]:
        return {"avgHighPrice", "avgLowPrice"}

    def provides(self) -> set[str]:
        return {"midpoint_price"}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df["midpoint_price"] = (df["avgHighPrice"] + df["avgLowPrice"]) / 2
        return df
