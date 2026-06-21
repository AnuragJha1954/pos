from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/orders/(?P<outlet_id>\w+)/$', consumers.OrderNotificationConsumer.as_asgi()),
]
