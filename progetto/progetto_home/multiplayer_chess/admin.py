from django.contrib import admin
from .models import *

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'photo']
    raw_id_fields = ['user']

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    ordering = ('-room_id',)

admin.site.register(ChessTournament)

