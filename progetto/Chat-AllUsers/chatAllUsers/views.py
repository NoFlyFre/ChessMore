from django.http import HttpResponse
from django.shortcuts import render

from .models import Message

def index(request):
    return render(request, 'chatAllUsers/index.html')

def room(request, room_name):
    username = request.GET.get('username', 'Guest') 
    messages = Message.objects.filter(room=room_name)[0:25] #25 numero colonne
    return render(request, 'chatAllUsers/room.html', {'room_name': room_name, 'username': username, 'messages': messages})