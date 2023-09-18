import io

import pandas as pd


def series_from_bytes(b: bytes) -> pd.Series:
    return pd.read_csv(io.BytesIO(b), index_col=0).iloc[:, 0]
