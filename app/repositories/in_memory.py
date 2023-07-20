from collections import defaultdict

from app.models.competiton import Competition, CompetitionId
from app.models.participant import Participant, ParticipantId
from app.models.submission import SubmissionResult
from app.repositories.common import CompetitionExists


class InMemoryDataRepository:
    _participants: dict[ParticipantId, Participant]
    _competitions: dict[CompetitionId, Competition]
    _submission_results: dict[CompetitionId, list[SubmissionResult]]

    def __init__(self) -> None:
        self._participants = {}
        self._competitions = {}
        self._submission_results = defaultdict(list)

    async def set_participant(self, participant: Participant | dict) -> None:
        obj = Participant.model_validate(participant)
        self._participants[obj.id] = obj

    async def get_participant(self, participant_id: ParticipantId) -> Participant | None:
        return self._participants.get(participant_id)

    async def set_competition(self, competition: Competition | dict) -> None:
        obj = Competition.model_validate(competition)
        if obj.id in self._competitions:
            raise CompetitionExists()
        self._competitions[obj.id] = obj

    async def get_competition(self, competition_id: CompetitionId) -> Competition | None:
        return self._competitions.get(competition_id)

    async def get_competitions(self) -> list[Competition]:
        return list(self._competitions.values())

    async def set_submission_result(self, submission_result: SubmissionResult) -> None:
        self._submission_results[submission_result.competition_id].append(submission_result)

    async def get_submission_results(self, competition_id: CompetitionId) -> list[SubmissionResult]:
        return self._submission_results[competition_id]
