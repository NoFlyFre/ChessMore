# Generated by Django 4.2 on 2023-04-30 20:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('multiplayer_chess', '0009_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('turn', models.CharField(choices=[('WHITE', 'White'), ('BLACK', 'Black')], default='White', max_length=5)),
                ('status', models.CharField(choices=[('ONGOING', 'Ongoing'), ('CHECKMATE', 'Checkmate'), ('DRAW', 'Draw')], default='ONGOING', max_length=10)),
                ('room_id', models.IntegerField(primary_key=True, serialize=False)),
                ('winner', models.CharField(blank=True, choices=[('WHITE', 'White'), ('BLACK', 'Black')], max_length=5, null=True)),
                ('player1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games_player1', to=settings.AUTH_USER_MODEL)),
                ('player2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games_player2', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='gameroom',
            name='players',
        ),
        migrations.RemoveField(
            model_name='gameroom',
            name='winner',
        ),
        migrations.RemoveField(
            model_name='player',
            name='friends',
        ),
        migrations.RemoveField(
            model_name='player',
            name='user',
        ),
        migrations.DeleteModel(
            name='Friend_Request',
        ),
        migrations.DeleteModel(
            name='Gameroom',
        ),
        migrations.DeleteModel(
            name='Player',
        ),
    ]
