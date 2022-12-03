from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from .routing import websocket_urlpatterns

# from .auth import JWTTokenAuthMiddleware
# websocket_router = JWTTokenAuthMiddleware(URLRouter(websocket_urlpatterns))

websocket_router = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
