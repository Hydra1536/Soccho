import asyncio
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_service.settings')

django_asgi_app = get_asgi_application()

from apps.notifications.events import run_pubsub_listener
from notification_service.routing import websocket_urlpatterns


class _NotificationASGIApp:
    def __init__(self):
        self.protocol_app = ProtocolTypeRouter(
            {
                'http': django_asgi_app,
                'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            }
        )
        self._event_task = None

    async def __call__(self, scope, receive, send):
        if self._event_task is None:
            self._event_task = asyncio.create_task(run_pubsub_listener())
        return await self.protocol_app(scope, receive, send)


application = _NotificationASGIApp()
