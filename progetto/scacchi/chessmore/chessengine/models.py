from django.db import models

class Game(models.Model):
    player1 = models.CharField(default="Placeholder", max_length=30)
    player2 = models.CharField(default="Placeholder", max_length=30)
    #status = models.CharField(default="ongoing")
    room_id = models.IntegerField(primary_key=True)
