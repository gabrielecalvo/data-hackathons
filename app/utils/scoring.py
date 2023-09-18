import pandas as pd

from app.models.evaluation import EvaluationMetricLogic


def score_submission(pred: pd.Series, actual: pd.Series, metric: EvaluationMetricLogic) -> float:
    return metric.func(pred, actual)
