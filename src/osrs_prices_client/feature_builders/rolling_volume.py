import pandas as pd

from ..model.feature_builder import FeatureBuilder


class RollingVolume(FeatureBuilder):
    """Aggregates wiki high/low volumes and computes a rolling average."""

    def __init__(
        self,
        high_volume_column: str,
        low_volume_column: str,
        window: int,
    ):
        if window <= 0:
            raise ValueError("window must be positive")
        self.high_volume_column = high_volume_column
        self.low_volume_column = low_volume_column
        self.window = window

    def get_name(self) -> str:
        return f"rolling_volume_{self.window}"

    def requires(self) -> set[str]:
        return {self.high_volume_column, self.low_volume_column}

    def provides(self) -> set[str]:
        return {"total_volume", f"{self.get_name()}_mean"}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df["total_volume"] = df[self.high_volume_column] + df[self.low_volume_column]
        df[f"{self.get_name()}_mean"] = df["total_volume"].rolling(self.window).mean()
        return df
