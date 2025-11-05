import pandas as pd

from ..model.feature_builder import FeatureBuilder


class ExponentialMovingAverage(FeatureBuilder):
    """Computes an exponential moving average over a provided source column."""

    def __init__(self, column: str, span: int):
        if span <= 0:
            raise ValueError("span must be positive")
        self.column = column
        self.span = span

    def get_name(self) -> str:
        return f"ema_{self.column}_{self.span}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        return {self.get_name()}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df[self.get_name()] = df[self.column].ewm(span=self.span, adjust=False).mean()
        return df
