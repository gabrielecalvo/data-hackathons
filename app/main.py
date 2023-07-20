from app.app import app
from app.constants import ROOT_PATH
from app.security.common import create_security_handler
from app.settings import Settings
from app.utils.repositories import create_repositories

settings = Settings(_env_file=ROOT_PATH / ".env", _env_file_encoding="utf-8")  # typing: ignore
app.state.security_handler = create_security_handler(settings)
app.state.repos = create_repositories(settings)
