# Generated by Django 4.2 on 2023-05-19 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multiplayer_chess', '0022_game_elo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='elo',
        ),
        migrations.AddField(
            model_name='game',
            name='elo_antichess',
            field=models.IntegerField(default=1000),
        ),
        migrations.AddField(
            model_name='game',
            name='elo_atomic',
            field=models.IntegerField(default=1000),
        ),
        migrations.AddField(
            model_name='game',
            name='elo_classic',
            field=models.IntegerField(default=1000),
        ),
    ]
