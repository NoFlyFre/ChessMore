# Generated by Django 4.2 on 2023-05-19 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multiplayer_chess', '0026_chesstournament'),
    ]

    operations = [
        migrations.AddField(
            model_name='chesstournament',
            name='mode',
            field=models.CharField(choices=[('classic', 'Classic'), ('atomic', 'Atomic'), ('antichess', 'Antichess')], max_length=13, null=True),
        ),
    ]
