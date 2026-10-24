from django.urls import re_path

from shop_chat import consumer


websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumer.ShopChatConsumer.as_asgi()),
]
