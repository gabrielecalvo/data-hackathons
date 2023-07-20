from app.constants import AZURE_WEBAPP_HEADER
from app.security.azure_webapp_header import BasicHeaderSecurity
from app.security.protocol import SecurityHandler
from app.settings import Settings


def create_security_handler(settings: Settings) -> SecurityHandler:
    if settings.PARTICIPANT_HANDLER == AZURE_WEBAPP_HEADER:
        return BasicHeaderSecurity(settings)
    else:
        raise AssertionError("unreachable")
