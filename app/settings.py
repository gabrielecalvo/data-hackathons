from pydantic_settings import BaseSettings

from app.constants import AZURE_WEBAPP_HEADER, IN_MEMORY


class Settings(BaseSettings):
    DATA_REPOSITORY_CONNECTION_STRING: str = IN_MEMORY
    PARTICIPANT_HANDLER: str = AZURE_WEBAPP_HEADER
    ADMIN_PARTICIPANT_IDS: str = ""
