import dataclasses
from collections.abc import Callable
from enum import Enum

import pandas as pd
from pydantic import BaseModel


class EvaluationMetric(str, Enum):
    RMSE = "rmse"


class EvaluationConfig(BaseModel):
    metric: EvaluationMetric
    feature_dataset_url: str
    target_dataset_url: str


@dataclasses.dataclass
class EvaluationMetricLogic:
    sort_multiplier: int  # -1: lower=better, +1: higher=better
    func: Callable[[pd.Series, pd.Series], float]


def _rmse_func(pred: pd.Series, actual: pd.Series) -> float:
    return ((pred - actual) ** 2).mean() ** 0.5


METRIC_LOGIC_MAP: dict[EvaluationMetric, EvaluationMetricLogic] = {
    EvaluationMetric.RMSE: EvaluationMetricLogic(func=_rmse_func, sort_multiplier=-1),
}

# check no missing mappings
assert set(EvaluationMetric) == set(METRIC_LOGIC_MAP), "Mismatch between EvaluationMetric and IS_BETTER_SCORE_MAP"
