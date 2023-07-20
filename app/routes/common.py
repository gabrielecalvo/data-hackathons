from pydantic import BaseModel, ConfigDict
from starlette.requests import Request

from app.models.participant import Participant
from app.security.protocol import SecurityHandler
from app.utils.repositories import DataRepositoryType


class AppState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: Request
    participant: Participant

    @property
    def data_repo(self) -> DataRepositoryType:
        return self.request.app.state.repos.data_repository

    @property
    def security_handler(self) -> SecurityHandler:
        return self.request.app.state.security_handler

    @property
    def base_content(self) -> dict:
        return {"request": self.request, "participant": self.participant}


async def get_appstate(request: Request) -> AppState:
    security_handler: SecurityHandler = request.app.state.security_handler
    participant = await security_handler.authorize_participant(request=request)
    return AppState(request=request, participant=participant)
