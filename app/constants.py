from pathlib import Path

from fastapi.templating import Jinja2Templates

IN_MEMORY = "in-memory"
AZURE_WEBAPP_HEADER = "azure-webapp-header"
APP_PATH = Path(__file__).parent
ROOT_PATH = APP_PATH.parent
TEMPLATES = Jinja2Templates(directory=str(APP_PATH / "templates"))
