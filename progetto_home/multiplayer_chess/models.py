from django.db import models
from django.conf import settings
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
import schedule
import time
from django.utils import timezone
import pytz
import threading
import datetime
from django.contrib.auth.models import User
from django.db .models import Max
import random
import secrets

scheduler_thread = None

class RunScheduleStart(threading.Thread):
    def __init__(self, instance_tour, time_start , sleep_interval=10):
        super().__init__()
        self._kill = threading.Event()
        self._interval = sleep_interval
        self.instance_tour = instance_tour
        self.time_start = time_start

    def run(self):
        schedule.every().day.at(self.time_start).do(crea_partite_ottavi, self.instance_tour)
        while True:
            schedule.run_pending()
            print(schedule.jobs) 
            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break

    def kill(self):
        self._kill.set()



class RunScheduleOttavi(threading.Thread):
    def __init__(self, instance_tour, sleep_interval=10):
        super().__init__()
        self._kill = threading.Event()
        self._interval = sleep_interval
        self.instance_tour = instance_tour

    def run(self):
        while True:
            print("running ottavi")
            game_list = list(self.instance_tour.matches.filter(bracket_position='A'))
            games_status = list(game.status for game in game_list)
            all_finished = all(status == 'finished' for status in games_status)
            if all_finished:
                crea_partite_quarti(self.instance_tour )

            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break 

    def kill(self):
        self._kill.set()


class RunScheduleQuarti(threading.Thread):
    def __init__(self, instance_tour, sleep_interval=10):
        super().__init__()
        self._kill = threading.Event()
        self._interval = sleep_interval
        self.instance_tour = instance_tour

    def run(self):
        while True:
            print("running quarti")
            game_list = list(self.instance_tour.matches.filter(bracket_position='B'))
            games_status = list(game.status for game in game_list)
            all_finished = all(status == 'finished' for status in games_status)
            if all_finished:
                crea_partite_semifinale(self.instance_tour )

            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break 

    def kill(self):
        self._kill.set()


class RunScheduleSemifinali(threading.Thread):
    def __init__(self, instance_tour, sleep_interval=10):
        super().__init__()
        self._kill = threading.Event()
        self._interval = sleep_interval
        self.instance_tour = instance_tour

    def run(self):
        while True:
            print("running semifinali")
            game_list = list(self.instance_tour.matches.filter(bracket_position='C'))
            games_status = list(game.status for game in game_list)
            all_finished = all(status == 'finished' for status in games_status)
            if all_finished:
                crea_partita_finale(self.instance_tour )

            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break

    def kill(self):
        self._kill.set()


class RunScheduleFinale(threading.Thread):
    def __init__(self, instance_tour, sleep_interval=10):
        super().__init__()
        self._kill = threading.Event()
        self._interval = sleep_interval
        self.instance_tour = instance_tour

    def run(self):
        while True:
            print("running finale")
            game_list = list(self.instance_tour.matches.filter(bracket_position='D'))
            games_status = list(game.status for game in game_list)
            all_finished = all(status == 'finished' for status in games_status)
            if all_finished:
                fine_torneo(self.instance_tour )

            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break 

    def kill(self):
        self._kill.set()




class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)
    elo_classic = models.IntegerField(default=1000)
    elo_atomic = models.IntegerField(default=1000)
    elo_antichess = models.IntegerField(default=1000)
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
    data_partita = models.DateTimeField(auto_now=True, null=True, blank=True) #auto_now permette di usare la data corrente nel momento che faccio game.save()
    TURN_CHOICES = [
        ('w', 'white'),
        ('b', 'black'),
    ]
    turn = models.CharField(max_length=1, choices=TURN_CHOICES, default='w')
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vincitore', on_delete=models.CASCADE, null=True, blank=True)
    STATUS_CHOICES= [
        ('created','Partita creata, in attesa dell\'avversario'),
        ('started','Partita iniziata'),
        ('finished','Partita terminata')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')
    elo_partita = models.IntegerField(null=True, blank=True)
    bracket_position = models.CharField(max_length=4, default = "", blank=True, null=True)
    numero_torneo = models.IntegerField(null=True, blank=True)
    
    class Meta: #modifico il comportamento del modello
        ordering = ['-data_partita'] #ordino per data (il meno sepcifica l'ordine decrescente)

    '''
    def __str__(self):
        return f"{self.player1.username} vs {self.player2.username} - {self.bracket_position} - {self.numero_torneo} - winner: {self.winner}"
    '''


class ChessTournament(models.Model):
    name = models.CharField(max_length=100)
    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True)
    players = models.ManyToManyField('Profile', related_name='tournaments', blank=True)
    MODE_CHOICES = [
        ('classic', 'Classic'),
        ('atomic', 'Atomic'),
        ('antichess', 'Antichess'),
    ]
    mode = models.CharField(max_length=13, choices=MODE_CHOICES, null=True)
    
    TIER_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('esperto', 'Esperto'),
    ]
    tier = models.CharField(max_length=13, choices=TIER_CHOICES, null=True)
    matches = models.ManyToManyField('Game', related_name='tournament', blank=True)

    STATUS_CHOICES = [
        ('iscrizione', 'Iscrizioni'),
        ('ottavi', 'Ottavi'),
        ('quarti', 'Quarti'),
        ('semifinale', 'Semifinale'),
        ('finale', 'Finale'),
        ('terminato', 'Terminato')
    ]
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, null=True)

def crea_partite_ottavi(instance):
    global scheduler_thread
    scheduler_thread.kill()
    

    instance.status = 'ottavi'
    player_list = list(instance.players.all())
    print(player_list)

    for i in range(8):
        
        max_id = Game.objects.aggregate(Max('room_id'))['room_id__max']

        player1 = secrets.choice(player_list)
        player_list.remove(player1)
        player2 = secrets.choice(player_list)
        player_list.remove(player2)

        game = Game.objects.create(
            player1= player1.user,
            player2= player2.user,
            room_id = max_id + 1,
            mode = 'classic', 
            status = 'started',
            bracket_position = 'A',
            numero_torneo = i
        )

        instance.matches.add(game)
        instance.save()

    scheduler_thread = RunScheduleOttavi(instance)
    scheduler_thread.start()
    return schedule.CancelJob

    




def crea_partite_quarti(instance):
    global scheduler_thread
    scheduler_thread.kill()

    instance.status = 'quarti'
    game_list = instance.matches.filter(bracket_position='A' )
    for i in range(4):
        game0 = game_list.filter(numero_torneo = i*2)[0] 
        game1 = game_list.filter(numero_torneo = i*2+1)[0]   
        max_id = Game.objects.aggregate(Max('room_id'))['room_id__max']

        game = Game.objects.create(
                player1= game1.winner,
                player2= game0.winner,
                room_id = max_id + 1,
                mode = instance.mode, 
                status = 'started',
                bracket_position = 'B',
                numero_torneo = 10 + i
        )
        
        instance.matches.add(game)

    instance.save()

    scheduler_thread = RunScheduleQuarti(instance)
    scheduler_thread.start()




def crea_partite_semifinale(instance):
    global scheduler_thread
    scheduler_thread.kill()
    instance.status = 'semifinale'

    game_list = instance.matches.filter(bracket_position='B')
    for i in range(2):
        game0 = game_list.filter(numero_torneo = 10 + i*2)[0] 
        game1 = game_list.filter(numero_torneo = 10 + i*2+1)[0]   
        max_id = Game.objects.aggregate(Max('room_id'))['room_id__max']

        game = Game.objects.create(
                player1= game1.winner,
                player2= game0.winner,
                room_id = max_id + 1,
                mode = instance.mode, 
                status = 'started',
                bracket_position = 'C',
                numero_torneo = 20 + i
        )
        
        instance.matches.add(game)

    instance.save()

    scheduler_thread = RunScheduleSemifinali(instance)
    scheduler_thread.start()



def crea_partita_finale(instance):
    global scheduler_thread
    scheduler_thread.kill()
    instance.status = 'finale'
    game_list = instance.matches.filter(bracket_position='C')
    
    game0 = game_list.filter(numero_torneo = 20)[0] 
    game1 = game_list.filter(numero_torneo = 21)[0]   
    max_id = Game.objects.aggregate(Max('room_id'))['room_id__max']

    game = Game.objects.create(
            player1= game1.winner,
            player2= game0.winner,
            room_id = max_id + 1,
            mode = instance.mode, 
            status = 'started',
            bracket_position = 'D',
            numero_torneo = 30
    )
        
    instance.matches.add(game)

    instance.save()

    scheduler_thread = RunScheduleFinale(instance)
    scheduler_thread.start()


def fine_torneo(instance):
    global scheduler_thread
    scheduler_thread.kill()
    instance.status = 'finished'



def run_schedule_semifinale(instance):
    while True:
        game_list = list(instance.matches.filter(bracket_position='C'))
        games_status = list(game.status for game in game_list)
        all_finished = all(status == 'finished' for status in games_status)
        time.sleep(10)

        if all_finished:
            crea_partita_finale(instance)      


def run_schedule_finale(instance):
    while True:
        game_list = list(instance.matches.filter(bracket_position='D'))
        games_status = list(game.status for game in game_list)
        all_finished = all(status == 'finished' for status in games_status)
        time.sleep(10)

        if all_finished:
            instance.status = 'finished' 
            scheduler_thread.cancel()


@receiver(post_save, sender=ChessTournament)
def create_tournament(sender, instance, created, **kwargs):
    global scheduler_thread  # Utilizziamo la variabile globale per il thread

    if created:
        time_start = (instance.start_datetime + datetime.timedelta(hours=2)).strftime('%H:%M:%S')

        # Crea un nuovo thread
        scheduler_thread = RunScheduleStart(instance, time_start)
        scheduler_thread.start()

        print(timezone.now())

