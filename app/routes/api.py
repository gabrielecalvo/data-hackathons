from http import HTTPStatus
from typing import Annotated, Any

import requests
from fastapi import APIRouter, Depends, HTTPException

import app.routes.paths as p
from app.models.competiton import Competition, CompetitionInbound
from app.models.evaluation import METRIC_LOGIC_MAP
from app.models.participant import Participant, Permission
from app.models.submission import Submission, SubmissionResult
from app.repositories.common import CompetitionExists
from app.routes.common import AppState, get_appstate
from app.utils.repositories import DataRepositoryType
from app.utils.scoring import score_submission

api_router = APIRouter()


def raise_404_if_null(obj: Any, entity: str = "entity") -> None:
    if obj is None:
        raise HTTPException(detail=f"{entity} not found", status_code=HTTPStatus.NOT_FOUND)


def ensure_scope(participant: Participant, permission: Permission) -> None:
    if permission not in participant.permissions:
        raise HTTPException(
            detail=f"Participant doesn't have the required permission: {permission}", status_code=HTTPStatus.FORBIDDEN
        )


@api_router.post(p.API_COMPETITION_SET, tags=["Competition"], response_model=Competition)
async def set_competition(
    appstate: Annotated[AppState, Depends(get_appstate)], competition: CompetitionInbound
) -> Competition:
    ensure_scope(participant=appstate.participant, permission=Permission.CREATE_COMPETITION)
    repo: DataRepositoryType = appstate.data_repo

    comp = Competition.from_inbound(competition)

    try:
        await repo.set_competition(comp)
    except CompetitionExists:
        raise HTTPException(
            detail="Could not generate unique id for competition. Try again.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    return comp


@api_router.get(p.API_COMPETITIONS_LIST, tags=["Competition"])
async def get_competitions(appstate: Annotated[AppState, Depends(get_appstate)]) -> list[Competition]:
    return await appstate.data_repo.get_competitions()


@api_router.get(p.API_COMPETITION_GET, tags=["Competition"])
async def get_competition(appstate: Annotated[AppState, Depends(get_appstate)], competition_id: str) -> Competition:
    competition = await appstate.data_repo.get_competition(competition_id)
    raise_404_if_null(competition, entity="Competition")
    assert isinstance(competition, Competition)
    return competition


@api_router.post(p.API_SUBMISSION_SET, tags=["Submission"], status_code=HTTPStatus.NO_CONTENT)
async def set_submission(appstate: Annotated[AppState, Depends(get_appstate)], submission: Submission) -> None:
    if appstate.participant.id != submission.participant_id:
        raise HTTPException(
            detail="Participant can not submit for other participants", status_code=HTTPStatus.FORBIDDEN
        )

    repo: DataRepositoryType = appstate.data_repo
    competition = await repo.get_competition(competition_id=submission.competition_id)
    raise_404_if_null(competition, entity="Competition")
    assert isinstance(competition, Competition)

    predicted: dict = submission.predictions
    actual: dict = requests.get(competition.evaluation.target_dataset_url).json()
    if actual.keys() != predicted.keys():
        _missing = set(actual).difference(predicted)
        _extra = set(predicted).difference(actual)
        err_msg = f"Submission prediction keys don't match the expected ones.\nMissing {_missing}\nExtra: {_extra}"
        raise HTTPException(detail=err_msg, status_code=HTTPStatus.BAD_REQUEST)

    metric = METRIC_LOGIC_MAP[competition.evaluation.metric]
    score = score_submission(pred=predicted, actual=actual, metric=metric)

    submission_result = SubmissionResult(
        competition_id=submission.competition_id,
        participant_id=submission.participant_id,
        submission_name=submission.name,
        score=score,
    )

    await repo.set_submission_result(submission_result=submission_result)


@api_router.get(p.API_SUBMISSION_RESULT_LIST, tags=["Submission"])
async def get_submission_results(
    appstate: Annotated[AppState, Depends(get_appstate)], competition_id: str
) -> list[SubmissionResult]:
    return await appstate.data_repo.get_submission_results(competition_id=competition_id)
