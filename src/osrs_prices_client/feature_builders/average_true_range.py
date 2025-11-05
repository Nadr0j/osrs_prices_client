import pandas as pd

from ..model.feature_builder import FeatureBuilder


class AverageTrueRange(FeatureBuilder):
    """Classic ATR computed from high/low/close inputs."""

    def __init__(
        self,
        high_column: str,
        low_column: str,
        close_column: str,
        window: int,
    ):
        if window <= 0:
            raise ValueError("window must be positive")
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.window = window

    def get_name(self) -> str:
        return f"atr_{self.window}"

    def requires(self) -> set[str]:
        return {self.high_column, self.low_column, self.close_column}

    def provides(self) -> set[str]:
        return {self.get_name()}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        high = df[self.high_column]
        low = df[self.low_column]
        close = df[self.close_column]

        prev_close = close.shift(1)
        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        df[self.get_name()] = tr.rolling(window=self.window).mean()
        return df
