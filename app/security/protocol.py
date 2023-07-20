from typing import Protocol

from fastapi import Request

from app.models.participant import Participant, ParticipantId


class SecurityHandler(Protocol):
    async def authorize_participant(self, request: Request) -> Participant:
        """
        Checks the request is authenticated and generates a participant
        object with the correct permissions
        """
        ...  # pragma: no cover

    async def get_participant(self, participant_id: ParticipantId) -> Participant:
        """Retrieves the information of a participant given the id"""
        ...  # pragma: no cover
