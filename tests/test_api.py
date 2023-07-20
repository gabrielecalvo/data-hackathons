from http import HTTPStatus

import pytest
import responses

import app.routes.paths as p
from app.models.competiton import Competition, CompetitionInbound
from app.models.submission import Submission
from tests.conftest import ADMIN_ID, SAMPLE_PARTICIPANT_ID, SAMPLE_UUID, make_header


@pytest.mark.freeze_uuids(values=[SAMPLE_UUID])
async def test_set_and_get_competitions(client, sample_competition_dict):
    inbound_load = CompetitionInbound.model_validate(sample_competition_dict).model_dump()
    expected_competition = Competition.model_validate(sample_competition_dict)
    r = await client.post(p.API_COMPETITION_SET, json=inbound_load, headers=make_header(ADMIN_ID))
    assert r.status_code == HTTPStatus.OK

    r = await client.get(p.API_COMPETITIONS_LIST)
    assert r.status_code == HTTPStatus.OK
    content = r.json()
    assert len(content) == 1
    assert Competition.model_validate(content[0]) == expected_competition

    r = await client.get(p.API_COMPETITION_GET.format(competition_id=SAMPLE_UUID))
    assert r.status_code == HTTPStatus.OK
    assert Competition.model_validate(r.json()) == expected_competition


async def test_404_if_nonexistent_competition(client):
    response = await client.get(p.API_COMPETITION_GET.format(competition_id="nope"))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.freeze_uuids(values=[SAMPLE_UUID], side_effect="cycle")
async def test_error_if_competition_id_collision(client, sample_competition_dict):
    c = Competition.model_validate(sample_competition_dict)

    # initial set
    r = await client.post(p.API_COMPETITION_SET, json=c.model_dump(), headers=make_header(ADMIN_ID))
    assert r.status_code == HTTPStatus.OK

    # same uuid generated by chance
    r = await client.post(p.API_COMPETITION_SET, json=c.model_dump(), headers=make_header(ADMIN_ID))
    assert r.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert r.json()["detail"] == "Could not generate unique id for competition. Try again."


async def test_normally_no_id_collisions(client, sample_competition_dict):
    c = Competition.model_validate(sample_competition_dict)

    for i in range(100):
        r = await client.post(p.API_COMPETITION_SET, json=c.model_dump(), headers=make_header(ADMIN_ID))
        assert r.status_code == HTTPStatus.OK


@responses.activate
async def test_set_submission_and_get_results(client, sample_competition: Competition):
    responses.add(
        responses.Response(method="GET", url=sample_competition.evaluation.target_dataset_url, json={"a": 1, "b": 2})
    )

    sample_submission = Submission(
        name="sample",
        competition_id=sample_competition.id,
        participant_id=SAMPLE_PARTICIPANT_ID,
        predictions={"a": 2, "b": 3},
    )

    r = await client.post(
        p.API_SUBMISSION_SET, json=sample_submission.model_dump(), headers=make_header(SAMPLE_PARTICIPANT_ID)
    )
    assert r.status_code == HTTPStatus.NO_CONTENT

    r = await client.get(p.API_SUBMISSION_RESULT_LIST.format(competition_id=sample_competition.id))
    assert r.status_code == HTTPStatus.OK
    assert r.json() == [
        {
            "competition_id": sample_competition.id,
            "participant_id": sample_submission.participant_id,
            "score": 1.0,
            "submission_name": sample_submission.name,
        }
    ]


@responses.activate
async def test_raise_on_set_invalid_submission(client, sample_competition: Competition):
    responses.add(
        responses.Response(method="GET", url=sample_competition.evaluation.target_dataset_url, json={"a": 1, "b": 2})
    )

    sample_submission = Submission(
        name="sample",
        competition_id=sample_competition.id,
        participant_id=SAMPLE_PARTICIPANT_ID,
        predictions={"w": 99, "b": 99},
    )

    r = await client.post(
        p.API_SUBMISSION_SET, json=sample_submission.model_dump(), headers=make_header(SAMPLE_PARTICIPANT_ID)
    )
    assert r.status_code == HTTPStatus.BAD_REQUEST
    assert (
        r.json()["detail"] == "Submission prediction keys don't match the expected ones.\nMissing {'a'}\nExtra: {'w'}"
    )
