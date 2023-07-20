import datetime as dt

from fastapi import Request

from app.models.participant import Participant, ParticipantId, Permission
from app.settings import Settings


class BasicHeaderSecurity:
    """
    Uses Azure WebApp injected header key (defined in `_header_key`) for authentication
    and authorisation.

    Access to the webapp is assumed handled by the Azure WebApp Microsoft Identity Provider
    Authorisation is very basic and allows all participants to see all pages and
    enter their own submissions. However, only admins can create competitions.

    Admin users can be defined by entering their ids in a comma separates sting as
    the environment variable ADMIN_PARTICIPANT_IDS.

    Participant are entirely based on the email in the injected header key.
    """

    _header_key = "x-ms-client-principal-name"
    _admin_ids: list[str]

    def __init__(self, settings: Settings) -> None:
        self._admin_ids = settings.ADMIN_PARTICIPANT_IDS.split(",")

    async def authorize_participant(self, request: Request) -> Participant:
        participant_id = request.headers.get(self._header_key, "unknown.guest@_")
        return await self.get_participant(participant_id=participant_id)

    async def get_participant(self, participant_id: ParticipantId) -> Participant:
        name, *_, lastname = participant_id.split("@")[0].split(".")
        return Participant(
            id=participant_id,
            name=f"{name.title()} {lastname.title()}",
            last_active=dt.datetime.utcnow(),
            permissions=set(Permission) if participant_id in self._admin_ids else set(),
        )
