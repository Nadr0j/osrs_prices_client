import pandas as pd

from ..model.feature_builder import FeatureBuilder


class BollingerBands(FeatureBuilder):
    """Rolling mean +/- k * std plus z-score."""

    def __init__(
        self,
        column: str,
        window: int,
        std_factor: float,
    ):
        if window <= 1:
            raise ValueError("window must be greater than 1")
        if std_factor <= 0:
            raise ValueError("std_factor must be positive")
        self.column = column
        self.window = window
        self.std_factor = std_factor

    def get_name(self) -> str:
        return f"bollinger_{self.column}_{self.window}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        base = self.get_name()
        return {f"{base}_upper", f"{base}_lower", f"{base}_zscore"}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        rolling = df[self.column].rolling(window=self.window)
        mean = rolling.mean()
        std = rolling.std(ddof=0)
        base = self.get_name()
        df[f"{base}_upper"] = mean + self.std_factor * std
        df[f"{base}_lower"] = mean - self.std_factor * std
        df[f"{base}_zscore"] = (df[self.column] - mean) / std
        return df
