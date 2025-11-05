import pandas as pd
from ..model.feature_builder import FeatureBuilder

class FeatureBuilderOrchestrator:
    """Orchestrates the scheduling and building of features using multiple FeatureBuilder instances."""
    @staticmethod
    def _schedule_feature_builders(data: pd.DataFrame, builders: list[FeatureBuilder]) -> list[FeatureBuilder]:
        available_features = set(data.columns)
        pending_feature_builders = list(builders)
        scheduled_feature_builders = list()

        while pending_feature_builders:
            progressed = False
            for builder in list(pending_feature_builders):
                if builder.requires().issubset(available_features):
                    scheduled_feature_builders.append(builder)
                    pending_feature_builders.remove(builder)
                    available_features.update(builder.provides())
                    progressed = True
            if not progressed: # We looped through all features and none were buildable
                missing = [builder.get_name() for builder in pending_feature_builders]
                raise ValueError("Unable to satisfy requirements for features: " + ", ".join(missing))
        
        return scheduled_feature_builders


    @staticmethod
    def _build_features_for_identifier(identifier_data: pd.DataFrame, builders: list[FeatureBuilder]) -> pd.DataFrame:
        scheduled_builders = FeatureBuilderOrchestrator._schedule_feature_builders(identifier_data, builders)
        df = identifier_data.copy()
        for builder in scheduled_builders:
            df = builder.build(df)
        return df


    @staticmethod
    def build_features(data: pd.DataFrame, builders: list[FeatureBuilder]) -> pd.DataFrame:
        identifiers = set([t[0] for t in list(data.columns)])
        df = data.copy()
        parts: list[pd.DataFrame] = list()

        for identifier in identifiers:
            identifier_data = df[identifier]
            identifier_data = FeatureBuilderOrchestrator._build_features_for_identifier(identifier_data, builders)
            identifier_data.columns = pd.MultiIndex.from_product([[identifier], identifier_data.columns])
            parts.append(identifier_data)
        
        return pd.concat(parts, axis=1)
    