import pandas as pd

from app.models.evaluation import EvaluationMetricLogic


def score_submission(pred: dict, actual: dict, metric: EvaluationMetricLogic) -> float:
    return metric.func(pd.Series(pred), pd.Series(actual))
