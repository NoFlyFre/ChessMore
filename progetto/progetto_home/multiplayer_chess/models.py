from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)
    def __str__(self):
        return f'Profile of {self.user.username}'

#--------------------------------------------------------------------------------------------------------------------

class Game(models.Model):
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='game_as_player1', on_delete=models.CASCADE, null=True)
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='game_as_player2', on_delete=models.CASCADE, null=True)
    room_id = models.IntegerField(primary_key=True)
    MODE_CHOICES = [
        ('classic', 'Classic'),
        ('atomic', 'Atomic'),
    ]
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, null=True)