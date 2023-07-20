import datetime as dt
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, Field

ParticipantId: TypeAlias = str


class Permission(str, Enum):
    CREATE_COMPETITION = "create_competition"


class Participant(BaseModel, extra="forbid"):
    id: ParticipantId
    name: str
    last_active: dt.datetime
    permissions: set[Permission] = Field(default=set())
