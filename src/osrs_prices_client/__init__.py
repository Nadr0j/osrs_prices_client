"""Public interface for the OSRS prices client."""

from .client import RealtimePricesClient, RealtimePricesThickClient
from .model import FeatureBuilder, InterpolationMethod, RealtimePricesRequest, Timestep
from .orchestrator import FeatureBuilderOrchestrator

# Module-level namespaces for discoverability and IDE-friendly autocomplete.
from . import client as clients
from . import feature_builders as features
from . import model as models
from . import orchestrator as orchestration

__all__ = [
    "RealtimePricesClient",
    "RealtimePricesThickClient",
    "FeatureBuilder",
    "InterpolationMethod",
    "RealtimePricesRequest",
    "Timestep",
    "FeatureBuilderOrchestrator",
    "clients",
    "features",
    "models",
    "orchestration",
]
