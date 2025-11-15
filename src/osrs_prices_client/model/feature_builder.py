from abc import ABC, abstractmethod
import pandas as pd


class FeatureBuilder(ABC):
    """Abstract base class for feature builders that define feature extraction logic.

    Realtime price data always arrives with the OSRS wiki base fields:
    avgHighPrice, avgLowPrice, highPriceVolume, and lowPriceVolume. Feature
    builders can rely on those columns being present before any derived
    features are computed.
    """

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def requires(self) -> set[str]:
        pass

    @abstractmethod
    def provides(self) -> set[str]:
        pass

    @abstractmethod
    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        pass
