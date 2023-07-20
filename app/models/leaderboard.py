from pydantic import BaseModel, Field


class LeaderBoardRow(BaseModel):
    position: int
    participant_name: str
    best_submission_name: str
    best_submission_score: float
    n_entries: int


class LeaderBoard(BaseModel):
    rows: list[LeaderBoardRow] = Field(default=[])
