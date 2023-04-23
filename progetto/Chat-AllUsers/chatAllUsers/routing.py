from django.urls import path, re_path

from . import consumers

websocket_urlpatterns = [
    #path('ws/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
    #path('ws//', consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()) 
] #modificare poi il file asgi.py