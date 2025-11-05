from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd
import pytest

from osrs_prices_client import FeatureBuilder, FeatureBuilderOrchestrator


@dataclass
class DummyBuilder(FeatureBuilder):
    name: str
    required: set[str]
    provided: set[str]
    transform: Callable[[pd.DataFrame], pd.DataFrame]

    def get_name(self) -> str:
        return self.name

    def requires(self) -> set[str]:
        return self.required

    def provides(self) -> set[str]:
        return self.provided

    def build(self, data: pd.DataFrame) -> pd.DataFrame:
        return self.transform(data.copy())


def test_schedule_orders_builders_by_dependencies():
    base_data = pd.DataFrame({"base": [1, 2, 3]})

    builder_a = DummyBuilder(
        name="A",
        required={"base"},
        provided={"feat_a"},
        transform=lambda df: df.assign(feat_a=df["base"] + 1),
    )
    builder_b = DummyBuilder(
        name="B",
        required={"feat_a"},
        provided={"feat_b"},
        transform=lambda df: df.assign(feat_b=df["feat_a"] * 2),
    )

    scheduled = FeatureBuilderOrchestrator._schedule_feature_builders(base_data, [builder_b, builder_a])

    assert scheduled == [builder_a, builder_b]


def test_build_features_runs_each_builder_per_identifier():
    data = pd.DataFrame(
        {
            ("item1", "base"): [1, 2],
            ("item2", "base"): [10, 20],
        }
    )
    data.columns = pd.MultiIndex.from_tuples(data.columns)

    builder = DummyBuilder(
        name="AddOne",
        required={"base"},
        provided={"feat_plus_one"},
        transform=lambda df: df.assign(feat_plus_one=df["base"] + 1),
    )

    result = FeatureBuilderOrchestrator.build_features(data, [builder])

    assert ("item1", "feat_plus_one") in result.columns
    assert ("item2", "feat_plus_one") in result.columns
    pd.testing.assert_series_equal(
        result[("item1", "feat_plus_one")],
        pd.Series([2, 3], name=("item1", "feat_plus_one")),
        check_dtype=False,
    )
    pd.testing.assert_series_equal(
        result[("item2", "feat_plus_one")],
        pd.Series([11, 21], name=("item2", "feat_plus_one")),
        check_dtype=False,
    )


def test_schedule_raises_when_requirements_unsatisfied():
    base_data = pd.DataFrame({"base": [1, 2, 3]})

    impossible_builder = DummyBuilder(
        name="Impossible",
        required={"missing"},
        provided={"new"},
        transform=lambda df: df.assign(new=df["missing"]),
    )

    with pytest.raises(ValueError) as exc:
        FeatureBuilderOrchestrator._schedule_feature_builders(base_data, [impossible_builder])

    assert "Impossible" in str(exc.value)

