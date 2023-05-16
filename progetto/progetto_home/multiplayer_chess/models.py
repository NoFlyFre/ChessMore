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
        ('antichess', 'Antichess'),
        ('kingofthehill', 'Kingofthehill'),
        ('threecheck', 'Threecheck'),
        ('horde', 'Horde'),
        ('racingkings', 'Racingkings')
    ]
    mode = models.CharField(max_length=13, choices=MODE_CHOICES, null=True)
    fen = models.TextField(null=True, default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    TURN_CHOICES = [
        ('w', 'white'),
        ('b', 'black'),
    ]
    turn = models.CharField(max_length=1, choices=TURN_CHOICES, default='w')
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vincitore', on_delete=models.CASCADE, null=True)
    STATUS_CHOICES= [
        ('created','Partita creata, in attesa dell\'avversario'),
        ('started','Partita iniziata'),
        ('finished','Partita terminata')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')
