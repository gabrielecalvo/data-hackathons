import dataclasses
from typing import TypeAlias

from azure.data.tables.aio import TableServiceClient

from app.constants import IN_MEMORY
from app.repositories.azure_storage import AzureStorageDataRepository
from app.repositories.in_memory import InMemoryDataRepository
from app.settings import Settings

DataRepositoryType: TypeAlias = InMemoryDataRepository | AzureStorageDataRepository


@dataclasses.dataclass
class Repositories:
    data_repository: DataRepositoryType


def create_repositories(settings: Settings) -> Repositories:
    data_repository: DataRepositoryType

    if settings.DATA_REPOSITORY_CONNECTION_STRING == IN_MEMORY:
        data_repository = InMemoryDataRepository()
    else:

        def aio_table_service_client_factory() -> TableServiceClient:
            return TableServiceClient.from_connection_string(settings.DATA_REPOSITORY_CONNECTION_STRING)

        data_repository = AzureStorageDataRepository(
            table_client_service_factory=aio_table_service_client_factory,
        )

    return Repositories(data_repository=data_repository)
