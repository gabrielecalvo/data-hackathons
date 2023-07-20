from app.constants import IN_MEMORY
from app.repositories.azure_storage import AzureStorageDataRepository
from app.repositories.in_memory import InMemoryDataRepository
from app.settings import Settings
from app.utils.repositories import create_repositories
from tests.conftest import AZURITE_CONNECTION_STRING


class TestCreateRepositories:
    @staticmethod
    def test_in_memory():
        actual = create_repositories(settings=Settings(DATA_REPOSITORY_CONNECTION_STRING=IN_MEMORY))
        assert isinstance(actual.data_repository, InMemoryDataRepository)

    @staticmethod
    def test_azurite():
        actual = create_repositories(settings=Settings(DATA_REPOSITORY_CONNECTION_STRING=AZURITE_CONNECTION_STRING))
        assert isinstance(actual.data_repository, AzureStorageDataRepository)
