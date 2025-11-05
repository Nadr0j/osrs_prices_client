import pandas as pd

from ..model.feature_builder import FeatureBuilder


class RateOfChange(FeatureBuilder):
    """n-period momentum style rate of change."""

    def __init__(self, column: str, window: int):
        if window <= 0:
            raise ValueError("window must be positive")
        self.column = column
        self.window = window

    def get_name(self) -> str:
        return f"roc_{self.column}_{self.window}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        return {self.get_name()}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df[self.get_name()] = df[self.column] / df[self.column].shift(self.window) - 1
        return df
