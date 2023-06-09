# Generated by Django 4.2 on 2023-05-22 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multiplayer_chess', '0031_remove_chesstournament_tier_chesstournament_elo_max_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chesstournament',
            name='elo_max',
        ),
        migrations.RemoveField(
            model_name='chesstournament',
            name='elo_min',
        ),
        migrations.RemoveField(
            model_name='chesstournament',
            name='matches',
        ),
        migrations.AddField(
            model_name='chesstournament',
            name='tier',
            field=models.CharField(choices=[('principiante', 'Principiante'), ('intermedio', 'Intermedio'), ('esperto', 'Esperto')], max_length=13, null=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='bracket_position',
            field=models.CharField(blank=True, default='', max_length=4, null=True),
        ),
    ]
