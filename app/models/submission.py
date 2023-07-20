from pydantic import BaseModel


class Submission(BaseModel):
    name: str
    competition_id: str
    participant_id: str
    predictions: dict


class SubmissionResult(BaseModel):
    competition_id: str
    participant_id: str
    submission_name: str
    score: float
