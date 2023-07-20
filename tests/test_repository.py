import datetime as dt

import pytest

from app.models.competiton import Competition
from app.models.participant import Participant
from app.models.submission import SubmissionResult
from app.repositories.common import CompetitionExists
from app.utils.repositories import Repositories


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_set_list_competition(repositories: Repositories, sample_competition: Competition):
    repo = repositories.data_repository
    assert await repo.get_competition(competition_id=sample_competition.id) is None
    await repo.set_competition(sample_competition)
    assert await repo.get_competition(competition_id=sample_competition.id) == sample_competition

    actual_competitions = await repo.get_competitions()
    assert len(actual_competitions) == 1
    assert actual_competitions[0] == sample_competition


@pytest.mark.integration
@pytest.mark.asyncio
async def test_raise_if_using_existing_competition_id(repositories: Repositories, sample_competition: Competition):
    repo = repositories.data_repository
    await repo.set_competition(sample_competition)

    with pytest.raises(CompetitionExists):
        await repo.set_competition(sample_competition)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_set_participant(repositories: Repositories):
    participant = Participant(id="1", name="bob", last_active=dt.datetime.utcnow())
    repo = repositories.data_repository
    assert await repo.get_participant(participant.id) is None
    await repo.set_participant(participant)
    assert await repo.get_participant(participant.id) == participant


@pytest.mark.integration
@pytest.mark.asyncio
async def test_set_list_submission_results(repositories: Repositories):
    submission_result = SubmissionResult(
        competition_id="competition_id",
        participant_id="participant_id",
        submission_name="submission_name",
        score=0,
    )
    repo = repositories.data_repository
    assert await repo.get_submission_results(submission_result.competition_id) == []
    await repo.set_submission_result(submission_result)
    assert await repo.get_submission_results(submission_result.competition_id) == [submission_result]
