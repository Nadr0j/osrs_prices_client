import math
import numpy as np
import pandas as pd

from ..model.feature_builder import FeatureBuilder


class RollingVolatility(FeatureBuilder):
    """Rolling standard deviation of log returns, optionally annualized."""

    def __init__(
        self,
        column: str,
        window: int,
        periods_per_year: int | None,
    ):
        if window <= 1:
            raise ValueError("window must be greater than 1")
        if periods_per_year is not None and periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive when provided")

        self.column = column
        self.window = window
        self.periods_per_year = periods_per_year

    def get_name(self) -> str:
        suffix = "_annualized" if self.periods_per_year else ""
        return f"rolling_volatility_{self.column}_{self.window}{suffix}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        return {self.get_name()}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        price = df[self.column]
        log_returns = np.log(price / price.shift(1))
        rolling_std = log_returns.rolling(self.window).std(ddof=0)

        if self.periods_per_year:
            rolling_std = rolling_std * math.sqrt(self.periods_per_year)

        df[self.get_name()] = rolling_std
        return df
