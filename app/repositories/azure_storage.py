import contextlib
import datetime as dt
from collections.abc import Callable
from typing import Any, TypeAlias

from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError
from azure.data.tables.aio import TableClient, TableServiceClient

from app.models.competiton import Competition, CompetitionId
from app.models.participant import Participant, ParticipantId
from app.models.submission import SubmissionResult
from app.repositories.common import CompetitionExists

TableServiceClientFactoryType: TypeAlias = Callable[[], TableServiceClient]


ALL = "all"


class TableNames:
    PARTICIPANT = "participant"
    COMPETITION = "competition"
    SUBMISSION_RESULT = "submissionresult"


async def ensure_table(table_service_client: TableServiceClient, table_name: str) -> TableClient:
    with contextlib.suppress(HttpResponseError):
        await table_service_client.create_table(table_name)

    return table_service_client.get_table_client(table_name=table_name)


class AzureStorageDataRepository:
    _table_service_client_factory: TableServiceClientFactoryType

    def __init__(
        self,
        table_client_service_factory: TableServiceClientFactoryType,
    ) -> None:
        self._table_service_client_factory = table_client_service_factory

    async def _simple_set_in_table(self, entity: Any, table_name: str, overwrite: bool = False) -> None:
        async with self._table_service_client_factory() as _table_service:
            tbl = await ensure_table(_table_service, table_name=table_name)
            _load = {"PartitionKey": ALL, "RowKey": entity.id, "Data": entity.model_dump_json()}
            if overwrite:
                await tbl.upsert_entity(_load)
            else:
                try:
                    await tbl.create_entity(_load)
                except ResourceExistsError:
                    raise CompetitionExists()

    async def _simple_get_from_table(self, entity_id: str, table_name: str) -> str | None:
        async with self._table_service_client_factory() as _table_service:
            tbl = await ensure_table(_table_service, table_name=table_name)
            try:
                entity = await tbl.get_entity(partition_key=ALL, row_key=entity_id)
            except ResourceNotFoundError:
                return None
        return entity["Data"]

    async def set_participant(self, participant: Participant) -> None:
        await self._simple_set_in_table(entity=participant, table_name=TableNames.PARTICIPANT, overwrite=True)

    async def get_participant(self, participant_id: ParticipantId) -> Participant | None:
        data = await self._simple_get_from_table(entity_id=participant_id, table_name=TableNames.PARTICIPANT)
        return None if data is None else Participant.model_validate_json(data)

    async def set_competition(self, competition: Competition) -> None:
        await self._simple_set_in_table(entity=competition, table_name=TableNames.COMPETITION)

    async def get_competition(self, competition_id: CompetitionId) -> Competition | None:
        data = await self._simple_get_from_table(entity_id=competition_id, table_name=TableNames.COMPETITION)
        return None if data is None else Competition.model_validate_json(data)

    async def get_competitions(self) -> list[Competition]:
        async with self._table_service_client_factory() as _table_service:
            tbl = await ensure_table(_table_service, table_name=TableNames.COMPETITION)
            entity_iterator = tbl.query_entities("PartitionKey eq @pk", parameters={"pk": ALL})
            return [Competition.model_validate_json(i["Data"]) async for i in entity_iterator]

    async def set_submission_result(self, submission_result: SubmissionResult) -> None:
        async with self._table_service_client_factory() as _table_service:
            tbl = await ensure_table(_table_service, table_name=TableNames.SUBMISSION_RESULT)
            await tbl.upsert_entity(
                {
                    "PartitionKey": submission_result.competition_id,
                    "RowKey": dt.datetime.utcnow().isoformat(),
                    "Data": submission_result.model_dump_json(),
                }
            )

    async def get_submission_results(self, competition_id: CompetitionId) -> list[SubmissionResult]:
        async with self._table_service_client_factory() as _table_service:
            tbl = await ensure_table(_table_service, table_name=TableNames.SUBMISSION_RESULT)
            entity_iterator = tbl.query_entities("PartitionKey eq @pk", parameters={"pk": competition_id})
            return [SubmissionResult.model_validate_json(i["Data"]) async for i in entity_iterator]
