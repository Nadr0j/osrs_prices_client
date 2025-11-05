import pandas as pd
from ..model.feature_builder import FeatureBuilder

class VolumeWeightedAveragePrice(FeatureBuilder):
    """FeatureBuilder that calculates the volume weighted average price from high and low price volumes."""
    def get_name(self) -> str:
        return "volume_weighted_average_price"
    
    def requires(self) -> set[str]:
        return set(["avgHighPrice", "avgLowPrice", "highPriceVolume", "lowPriceVolume"])

    def provides(self) -> set[str]:
        return set(["volume_weighted_average_price"])

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df["volume_weighted_average_price"] = (df["avgHighPrice"] * df["highPriceVolume"] + df["avgLowPrice"] * df["lowPriceVolume"]) / (df["highPriceVolume"] + df["lowPriceVolume"])
        return df