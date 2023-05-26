# Generated by Django 4.2 on 2023-05-19 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multiplayer_chess', '0023_remove_game_elo_game_elo_antichess_game_elo_atomic_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='elo_antichess',
        ),
        migrations.RemoveField(
            model_name='game',
            name='elo_atomic',
        ),
        migrations.RemoveField(
            model_name='game',
            name='elo_classic',
        ),
        migrations.AddField(
            model_name='profile',
            name='elo_antichess',
            field=models.IntegerField(default=1000),
        ),
        migrations.AddField(
            model_name='profile',
            name='elo_atomic',
            field=models.IntegerField(default=1000),
        ),
        migrations.AddField(
            model_name='profile',
            name='elo_classic',
            field=models.IntegerField(default=1000),
        ),
    ]
