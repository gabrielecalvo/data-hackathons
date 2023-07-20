import uuid
from typing import TypeAlias

from pydantic import BaseModel, Field

from app.models.evaluation import EvaluationConfig

CompetitionId: TypeAlias = str


class _DataObject(BaseModel):
    description: str
    url: str


class CompetitionInbound(BaseModel):
    name: str
    description: str = ""
    data: list[_DataObject] = Field(default=[])
    evaluation: EvaluationConfig
    tags: list[str] = Field(default=[])


class Competition(CompetitionInbound):
    id: CompetitionId = ""

    @classmethod
    def from_inbound(cls, competition_inbound: CompetitionInbound) -> "Competition":
        data = competition_inbound.model_dump() | {"id": str(uuid.uuid4())}
        return cls.model_validate(data)
