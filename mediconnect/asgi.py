"""
ASGI config for mediconnect project — Django Channels entry point.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediconnect.settings')

django_asgi_app = get_asgi_application()

import consultations.routing  # noqa: E402 — must import after Django setup

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(consultations.routing.websocket_urlpatterns)
    ),
})
