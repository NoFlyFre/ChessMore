# Generated by Django 4.2 on 2023-05-16 02:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('multiplayer_chess', '0017_game_turn'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='status',
            field=models.CharField(choices=[('w', 'white'), ('b', 'black')], default='created', max_length=10),
        ),
        migrations.AddField(
            model_name='game',
            name='winner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vincitore', to=settings.AUTH_USER_MODEL),
        ),
    ]
