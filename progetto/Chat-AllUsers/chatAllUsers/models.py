from django.db import models

class Message(models.Model):
    username = models.CharField(max_length=255)
    room = models.CharField(max_length=255)
    data = models.TextField() #messaggio
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta: #modifico il comportamento del modello
        ordering = ('date_added',) #ordino per data