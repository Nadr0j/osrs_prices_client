import pandas as pd

from ..model.feature_builder import FeatureBuilder


class RollingMean(FeatureBuilder):
    """Simple moving average over a window."""

    def __init__(self, column: str, window: int, min_periods: int | None):
        if window <= 0:
            raise ValueError("window must be positive")
        self.column = column
        self.window = window
        self.min_periods = min_periods if min_periods is not None else window

    def get_name(self) -> str:
        return f"rolling_mean_{self.column}_{self.window}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        return {self.get_name()}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df[self.get_name()] = (
            df[self.column].rolling(window=self.window, min_periods=self.min_periods).mean()
        )
        return df
