import contextlib
from pathlib import Path

import pytest
from azure.core.exceptions import HttpResponseError
from fastapi import FastAPI
from httpx import AsyncClient

from app.app import app
from app.constants import IN_MEMORY
from app.models.competiton import Competition
from app.models.participant import ParticipantId
from app.repositories.azure_storage import TableNames, TableServiceClientFactoryType
from app.routes import paths as p
from app.security.azure_webapp_header import BasicHeaderSecurity
from app.settings import Settings
from app.utils.repositories import Repositories, create_repositories

TEST_DATA_FLD = Path(__file__).parent / "data"
AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
)
ADMIN_ID = "admin.id@"
SAMPLE_PARTICIPANT_ID = "sample.participant@"
SAMPLE_UUID = "11111111-1111-1111-1111-111111111111"

with open(TEST_DATA_FLD / "sample_target.csv") as f:
    SAMPLE_ACTUAL_SER_CSV = f.read()


@pytest.fixture
def sample_competition_dict():
    return {
        "id": SAMPLE_UUID,
        "name": "Sample Competition",
        "description": "Predict y given X",
        "data": [
            {"description": "Training data features", "url": "https://X_test.example-site.com"},
            {"description": "Training data target", "url": "https://y_test.example-site.com"},
            {"description": "Test data features", "url": "https://X_train.example-site.com"},
            {"description": "Test data target", "url": "https://y_train.example-site.com"},
        ],
        "evaluation": {
            "metric": "rmse",
            "feature_dataset_url": "https://X_eval.example-site.com",
            "target_dataset_url": "https://y_eval.example-site.com",
        },
        "tags": ["timeseries", "ml"],
    }


class AsyncTestClient(AsyncClient):
    app: FastAPI


def make_header(participant_id: ParticipantId) -> dict[str, str]:
    return {"x-ms-client-principal-name": participant_id}


@pytest.fixture
def basic_security_handler() -> BasicHeaderSecurity:
    return BasicHeaderSecurity(settings=Settings(ADMIN_PARTICIPANT_IDS=ADMIN_ID))


@pytest.fixture
def client(basic_security_handler) -> AsyncTestClient:
    app.state.repos = create_repositories(settings=Settings(DATA_REPOSITORY_CONNECTION_STRING=IN_MEMORY))
    app.state.security_handler = basic_security_handler
    _client = AsyncTestClient(app=app, base_url="http://test")
    _client.app = app
    return _client


@pytest.fixture
async def sample_competition(client, sample_competition_dict) -> Competition:
    r = await client.post(p.API_COMPETITION_SET, json=sample_competition_dict, headers=make_header(ADMIN_ID))
    r.raise_for_status()
    r = await client.get(p.API_COMPETITIONS_LIST)
    r.raise_for_status()
    return Competition.model_validate(r.json()[0])


@pytest.fixture(params=["in-memory", "azure-storage"])
async def repositories(request) -> Repositories:
    repos: Repositories
    if request.param == "azure-storage":
        repos = create_repositories(settings=Settings(DATA_REPOSITORY_CONNECTION_STRING=AZURITE_CONNECTION_STRING))
        await delete_table(repos.data_repository._table_service_client_factory, TableNames.PARTICIPANT)
        await delete_table(repos.data_repository._table_service_client_factory, TableNames.COMPETITION)
        await delete_table(repos.data_repository._table_service_client_factory, TableNames.SUBMISSION_RESULT)
    else:
        repos = create_repositories(settings=Settings(DATA_REPOSITORY_CONNECTION_STRING=IN_MEMORY))
    return repos


async def delete_table(table_service_client_factory: TableServiceClientFactoryType, table_name: str) -> None:
    async with table_service_client_factory() as table_service_client:
        with contextlib.suppress(HttpResponseError):
            await table_service_client.delete_table(table_name)
