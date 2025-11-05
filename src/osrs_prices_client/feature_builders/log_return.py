import numpy as np
import pandas as pd

from ..model.feature_builder import FeatureBuilder


class LogReturn(FeatureBuilder):
    """Computes backward-looking log returns for configurable horizons."""

    def __init__(self, column: str, horizons: list[int]):
        self.column = column
        if not horizons:
            raise ValueError("horizons must be provided")
        if any(h <= 0 for h in horizons):
            raise ValueError("All horizons must be positive integers")
        self.horizons = horizons

    def get_name(self) -> str:
        return f"log_return_{self.column}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        return {f"{self.get_name()}_{h}" for h in self.horizons}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        price = df[self.column]
        for horizon in self.horizons:
            shifted = price.shift(horizon)
            df[f"{self.get_name()}_{horizon}"] = np.log(price / shifted)
        return df
