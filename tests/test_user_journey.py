import io
from http import HTTPStatus

import pandas as pd
import responses

import app.routes.paths as p
from app.models.competiton import Competition, CompetitionInbound
from app.models.submission import Submission
from app.utils.parse_csv import series_from_bytes
from tests.conftest import ADMIN_ID, SAMPLE_ACTUAL_SER_CSV, SAMPLE_PARTICIPANT_ID, make_header


async def test_reach_home_with_user_name(client):
    expected = '<a class="nav-link">Someone Else</a>'
    response = await client.get(p.WEB_ROOT, headers={"x-ms-client-principal-name": "someone.else@gmail.com"})
    assert response.status_code == 200
    assert expected in response.text


async def test_only_admin_can_set_competition(client, sample_competition_dict):
    comp = Competition.model_validate(sample_competition_dict)
    r = await client.post(p.API_COMPETITION_SET, json=comp.model_dump(), headers=make_header(SAMPLE_PARTICIPANT_ID))
    assert r.status_code == HTTPStatus.FORBIDDEN
    assert r.json()["detail"] == "Participant doesn't have the required permission: Permission.CREATE_COMPETITION"

    r = await client.post(p.API_COMPETITION_SET, json=comp.model_dump(), headers=make_header(ADMIN_ID))
    assert r.status_code == HTTPStatus.OK


async def test_empty_competition_page_shows_empty_message(client):
    response = await client.get(p.WEB_COMPETITIONS_LIST)
    assert response.status_code == HTTPStatus.OK
    assert "No competitions found" in response.text


async def test_empty_competition_page_for_inexistent_competition(client):
    response = await client.get(p.WEB_COMPETITION_GET.format(competition_id="non-existent"))
    assert response.status_code == HTTPStatus.OK
    assert "Competition not found :(" in response.text


async def test_list_sample_competitions(client, sample_competition_dict):
    evaluation = sample_competition_dict["evaluation"]
    c1 = CompetitionInbound(name="Sample Competition A", evaluation=evaluation)
    c2 = CompetitionInbound(name="Sample Competition B", evaluation=evaluation)
    (await client.post(p.API_COMPETITION_SET, json=c1.model_dump(), headers=make_header(ADMIN_ID))).raise_for_status()
    (await client.post(p.API_COMPETITION_SET, json=c2.model_dump(), headers=make_header(ADMIN_ID))).raise_for_status()

    r = await client.get(p.API_COMPETITIONS_LIST)
    r.raise_for_status()
    competitions = [Competition.model_validate(i) for i in r.json()]

    response = await client.get(p.WEB_COMPETITIONS_LIST)
    assert response.status_code == HTTPStatus.OK
    for c in competitions:
        assert c.name in response.text
        assert f'href="/competition/{c.id}"' in response.text


async def test_browse_competition_page(client, sample_competition: Competition):
    response = await client.get(p.WEB_COMPETITION_GET.format(competition_id=sample_competition.id))
    assert response.status_code == HTTPStatus.OK
    for info in (
        sample_competition.name,
        sample_competition.description,
        *sample_competition.tags,
        *[i.description for i in sample_competition.data],
        *[i.url for i in sample_competition.data],
        sample_competition.evaluation.metric.value,
        sample_competition.evaluation.feature_dataset_url,
    ):
        assert info in response.text

    assert sample_competition.evaluation.target_dataset_url not in response.text


@responses.activate
async def test_raise_on_submissions_with_wrong_keys(client, sample_competition: Competition):
    responses.add(
        responses.Response(
            method="GET", url=sample_competition.evaluation.target_dataset_url, body=SAMPLE_ACTUAL_SER_CSV
        )
    )
    err_msg = "Submission prediction keys don't match the expected ones.\nMissing {'b'}\nExtra: {'d'}"

    response = await client.post(
        p.WEB_COMPETITION_SUBMIT.format(competition_id=sample_competition.id),
        data={"name": "Wrong key d instead of b"},
        files={"predictions": ("wrong.csv", b"C1,C2\na,1\nd,2")},
        headers=make_header(SAMPLE_PARTICIPANT_ID),
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == err_msg


@responses.activate
async def test_raise_on_submissions_of_invalid_data(client, sample_competition: Competition):
    responses.add(
        responses.Response(
            method="GET", url=sample_competition.evaluation.target_dataset_url, body=SAMPLE_ACTUAL_SER_CSV
        )
    )
    err_msg = "Could not load and parse the data. Check it is formatted according to the submission template."

    response = await client.post(
        p.WEB_COMPETITION_SUBMIT.format(competition_id=sample_competition.id),
        data={"name": "Wrong key d instead of b"},
        files={"predictions": ("wrong.csv", b"this is not a csv")},
        headers=make_header(SAMPLE_PARTICIPANT_ID),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == err_msg


@responses.activate
async def test_raise_on_submissions_null_data(client, sample_competition: Competition):
    responses.add(
        responses.Response(
            method="GET", url=sample_competition.evaluation.target_dataset_url, body=SAMPLE_ACTUAL_SER_CSV
        )
    )
    err_msg = "Found 1 null values in the submitted data. Please fill the NaN with whichever logic you think is fit."

    response = await client.post(
        p.WEB_COMPETITION_SUBMIT.format(competition_id=sample_competition.id),
        data={"name": "Wrong key d instead of b"},
        files={"predictions": ("withnulls.csv", b"C1,C2\na,\nb,3")},
        headers=make_header(SAMPLE_PARTICIPANT_ID),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == err_msg


@responses.activate
async def test_submissions_to_leaderboard(client, sample_competition: Competition):
    responses.add(
        responses.Response(
            method="GET", url=sample_competition.evaluation.target_dataset_url, body=SAMPLE_ACTUAL_SER_CSV
        )
    )
    participant1_id = "ann.bee@c.d"
    participant2_id = "chris.doo@c.d"

    # No submission to start with
    response = await client.get(p.WEB_COMPETITION_GET.format(competition_id=sample_competition.id))
    assert "No submissions yet" in response.text

    # First Ann's Submission
    response = await client.post(
        p.WEB_COMPETITION_SUBMIT.format(competition_id=sample_competition.id),
        data={"name": "Ann's first"},
        files={"predictions": ("A1.csv", b"C1,C2\na,2\nb,3")},
        headers=make_header(participant1_id),
    )
    actual = pd.read_html(io.StringIO(response.text))[0].to_dict(orient="index")
    expected = {0: {"#": 1, "Name": "Ann Bee", "Best Score": 1.0, "Best Submission": "Ann's first", "No Entries": 1}}
    assert actual == expected

    # First Chris' Submission
    response = await client.post(
        p.WEB_COMPETITION_SUBMIT.format(competition_id=sample_competition.id),
        data={"name": "Chris's first"},
        files={"predictions": ("C1.csv", b"C1,C2\na,2\nb,2")},
        headers=make_header(participant2_id),
    )
    actual = pd.read_html(io.StringIO(response.text))[0].to_dict(orient="index")
    expected = {
        0: {"#": 1, "Name": "Chris Doo", "Best Score": 0.707, "Best Submission": "Chris's first", "No Entries": 1},
        1: {"#": 2, "Name": "Ann Bee", "Best Score": 1.0, "Best Submission": "Ann's first", "No Entries": 1},
    }
    assert actual == expected

    # Second Ann's Submission
    response = await client.post(
        p.WEB_COMPETITION_SUBMIT.format(competition_id=sample_competition.id),
        data={"name": "Ann's second"},
        files={"predictions": ("A2.csv", b"C1,C2\na,1\nb,2")},
        headers=make_header(participant1_id),
    )
    actual = pd.read_html(io.StringIO(response.text))[0].to_dict(orient="index")
    expected = {
        0: {"#": 1, "Name": "Ann Bee", "Best Score": 0.0, "Best Submission": "Ann's second", "No Entries": 2},
        1: {"#": 2, "Name": "Chris Doo", "Best Score": 0.707, "Best Submission": "Chris's first", "No Entries": 1},
    }
    assert actual == expected


@responses.activate
async def test_cannot_submit_for_other_partecipants(client, sample_competition: Competition):
    responses.add(
        responses.Response(
            method="GET", url=sample_competition.evaluation.target_dataset_url, body=SAMPLE_ACTUAL_SER_CSV
        )
    )

    r = await client.post(
        p.API_SUBMISSION_SET,
        json=Submission(
            name="Ann's first",
            competition_id=sample_competition.id,
            participant_id="other.participant@a.b",
            predictions={"a": 2, "b": 3},
        ).model_dump(),
        headers=make_header(SAMPLE_PARTICIPANT_ID),
    )
    assert r.status_code == HTTPStatus.FORBIDDEN
    assert r.json()["detail"] == "Participant can not submit for other participants"


@responses.activate
async def test_can_get_submit_template(client, sample_competition: Competition):
    sample_actual_ser = pd.Series([1, 2], name="val", index=["a", "b"]).rename_axis("idx")
    expected_template_ser = sample_actual_ser.mask([True] * len(sample_actual_ser))

    responses.add(
        responses.Response(
            method="GET", url=sample_competition.evaluation.target_dataset_url, body=sample_actual_ser.to_csv()
        )
    )

    response = await client.get(p.API_SUBMISSION_TEMPLATE_GET.format(competition_id=sample_competition.id))
    response.raise_for_status()
    template_ser = series_from_bytes(response.content)
    pd.testing.assert_series_equal(template_ser, expected_template_ser)
