import os
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Aggiunge ai-service al path Python (funziona sia in locale che in Docker)
AI_SERVICE_PATH = str(Path(__file__).resolve().parent.parent.parent / 'ai-service')
if AI_SERVICE_PATH not in sys.path:
    sys.path.insert(0, AI_SERVICE_PATH)

from django.core.asgi import get_asgi_application

django_app = get_asgi_application()

from main import app as fastapi_app  # importato DOPO django setup

# Prefissi URL gestiti da FastAPI
_FASTAPI_PREFIXES = ('/ai', '/reports', '/health')


class SmartCRMASGI:
    """Smista le richieste tra Django e FastAPI in base al prefisso URL."""

    async def __call__(self, scope, receive, send):
        if scope['type'] in ('http', 'websocket'):
            path = scope.get('path', '')
            if any(path.startswith(p) for p in _FASTAPI_PREFIXES):
                await fastapi_app(scope, receive, send)
                return
        await django_app(scope, receive, send)


application = SmartCRMASGI()
