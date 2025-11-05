import pandas as pd

from ..model.feature_builder import FeatureBuilder


class LagFeature(FeatureBuilder):
    """Creates lagged copies of a source column for autoregressive modeling."""

    def __init__(
        self,
        column: str,
        lags: list[int],
        fill_method: str | None,
    ):
        self.column = column
        if not lags:
            raise ValueError("lags must be provided")
        if any(lag <= 0 for lag in lags):
            raise ValueError("All lags must be positive integers")
        self.lags = lags
        if fill_method not in {None, "ffill"}:
            raise ValueError('fill_method must be None or "ffill"')
        self.fill_method = fill_method

    def get_name(self) -> str:
        return f"lag_{self.column}"

    def requires(self) -> set[str]:
        return {self.column}

    def provides(self) -> set[str]:
        return {f"{self.get_name()}_{lag}" for lag in self.lags}

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        source = df[self.column]
        for lag in self.lags:
            lagged = source.shift(lag)
            if self.fill_method == "ffill":
                lagged = lagged.ffill()
                lagged = lagged.fillna(source.iloc[0])
            df[f"{self.get_name()}_{lag}"] = lagged
        return df
