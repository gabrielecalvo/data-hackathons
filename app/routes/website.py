from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

import app.routes.paths as p
from app.constants import TEMPLATES
from app.models.competiton import Competition
from app.models.evaluation import METRIC_LOGIC_MAP
from app.models.leaderboard import LeaderBoard, LeaderBoardRow
from app.models.participant import ParticipantId
from app.models.submission import Submission
from app.routes.api import get_competition, get_competitions, get_submission_results, set_submission
from app.routes.common import AppState, get_appstate
from app.security.protocol import SecurityHandler
from app.utils.parse_csv import series_from_bytes

website_router = APIRouter(include_in_schema=False)


@website_router.get(p.WEB_ROOT)
async def home(appstate: Annotated[AppState, Depends(get_appstate)]) -> Any:
    return TEMPLATES.TemplateResponse("home.html", appstate.base_content)


@website_router.get(p.WEB_COMPETITIONS_LIST)
async def competition_list(appstate: Annotated[AppState, Depends(get_appstate)]) -> Any:
    competitions = await get_competitions(appstate=appstate)
    return TEMPLATES.TemplateResponse("competitions.html", appstate.base_content | {"competitions": competitions})


@website_router.get(p.WEB_COMPETITION_GET)
async def competition_detail(competition_id: str, appstate: Annotated[AppState, Depends(get_appstate)]) -> Any:
    try:
        competition = await get_competition(appstate=appstate, competition_id=competition_id)
    except HTTPException:
        return TEMPLATES.TemplateResponse("competition.html", appstate.base_content | {"competition": None})

    assert isinstance(competition, Competition)
    leaderboard = await _build_leaderboard(competition=competition, appstate=appstate)
    return TEMPLATES.TemplateResponse(
        "competition.html", appstate.base_content | {"competition": competition, "leaderboard": leaderboard}
    )


async def _build_leaderboard(competition: Competition, appstate: AppState) -> LeaderBoard | None:
    submission_results = await get_submission_results(appstate=appstate, competition_id=competition.id)
    if not submission_results:
        return None

    metric = METRIC_LOGIC_MAP[competition.evaluation.metric]
    participant_rows: dict[ParticipantId, LeaderBoardRow] = {}
    security_handler: SecurityHandler = appstate.security_handler
    for sr in submission_results:
        if sr.participant_id not in participant_rows:
            _participant = await security_handler.get_participant(participant_id=sr.participant_id)

            participant_rows[sr.participant_id] = LeaderBoardRow(
                position=-1,
                participant_name=_participant.name,
                best_submission_name=sr.submission_name,
                best_submission_score=sr.score,
                n_entries=1,
            )
        else:
            _row = participant_rows[sr.participant_id]
            _row.n_entries += 1
            if metric.sort_multiplier * sr.score > metric.sort_multiplier * _row.best_submission_score:
                _row.best_submission_name = sr.submission_name
                _row.best_submission_score = sr.score

    sorted_rows = sorted(participant_rows.values(), key=lambda x: -metric.sort_multiplier * x.best_submission_score)
    positioned_rows = []
    for i, row in enumerate(sorted_rows):
        row.position = i + 1
        positioned_rows.append(row)

    return LeaderBoard(rows=positioned_rows)


@website_router.post(p.WEB_COMPETITION_SUBMIT)
async def competition_submit(
    competition_id: str,
    name: Annotated[str, Form()],
    predictions: Annotated[UploadFile, File()],
    appstate: Annotated[AppState, Depends(get_appstate)],
) -> Any:
    try:
        pred_ser = series_from_bytes(await predictions.read())
    except Exception:
        raise HTTPException(
            detail="Could not load and parse the data. Check it is formatted according to the submission template.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    if nulls := pred_ser.isna().sum():
        raise HTTPException(
            detail=f"Found {nulls} null values in the submitted data. "
            f"Please fill the NaN with whichever logic you think is fit.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    submission = Submission(
        name=name,
        competition_id=competition_id,
        participant_id=appstate.participant.id,
        predictions=pred_ser.to_dict(),
    )
    await set_submission(appstate=appstate, submission=submission)
    return await competition_detail(competition_id=competition_id, appstate=appstate)
