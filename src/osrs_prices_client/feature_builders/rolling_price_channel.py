import pandas as pd

from ..model.feature_builder import FeatureBuilder


class RollingPriceChannel(FeatureBuilder):
    """Tracks rolling high/low for breakout-style signals."""

    def __init__(self, column: str, window: int):
        if window <= 0:
            raise ValueError("window must be positive")
        self.column = column
        self.window = window

    def get_name(self) -> str:
        return f"price_channel_{self.column}_{self.window}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        base = self.get_name()
        return {f"{base}_high", f"{base}_low"}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        rolling = df[self.column].rolling(window=self.window, min_periods=1)
        base = self.get_name()
        df[f"{base}_high"] = rolling.max()
        df[f"{base}_low"] = rolling.min()
        return df
