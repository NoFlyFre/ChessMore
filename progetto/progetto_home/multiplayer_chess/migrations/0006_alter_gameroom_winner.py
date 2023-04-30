# Generated by Django 3.2.6 on 2022-01-23 15:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('multiplayer_chess', '0005_alter_gameroom_winner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameroom',
            name='winner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner', to='multiplayer_chess.player'),
        ),
    ]