from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import HttpResponse
from .forms import *
from .models import *
from .filters import FilterCronologia
import json
import re
from django.urls import reverse

def index(request):
    if request.user.is_authenticated:
        return redirect('multiplayer_chess:home')
    return redirect('multiplayer_chess:login')

def loginView(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("multiplayer_chess:home")
        else:
            messages.error(request, "username o password errati; riprovare.")
    form = LoginForm()
    return render(request=request, template_name="multiplayer_chess/login.html", context={"login_form": form})

def logoutView(request):
    logout(request)
    messages.success(request, "hai eseguito il log-out con successo.")
    return redirect("multiplayer_chess:login")

def registerView(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            messages.success(request, "registrazione avvenuta con successo; adesso, acceda al suo profilo.")
            return redirect("multiplayer_chess:login")
        else:
            html_error = form.errors.as_text()
            new_html_error = re.sub(r'\*[^*]+\*', '', html_error).strip()
            messages.error(request, f"qualcosa è andato storto durante la registrazione: {new_html_error}")
    form = RegisterForm()
    return render(request=request, template_name="multiplayer_chess/register.html", context={"register_form": form})


@cache_control(no_cache=True, max_age=1)
def home(request):  
    if request.user.is_authenticated:
        return render(request=request, template_name='multiplayer_chess/home.html')
    elif 'username' in request.COOKIES and 'password' in request.COOKIES:
        username = request.COOKIES['username']
        password = request.COOKIES['password']
        user = authenticate(username=username, password=password)
        if user is None:
            user_created =get_user_model().objects.create_user(
                username=username,
                password=password,
            )
            Profile.objects.create(
                user=user_created,
            )   
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request=request, template_name='multiplayer_chess/home.html')
        else:
            return redirect("multiplayer_chess:login")
    else:
        return redirect("multiplayer_chess:login")

@login_required(login_url='/login')
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        try:
            user_form.save()
            profile_form.save()
            messages.success(request, "profilo modificato con successo.")
        except Exception as e:
            messages.error(request, "qualcosa è andato storto durante la modifica; riprovare.")
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request, 'multiplayer_chess/edit.html', context={'user_form': user_form, 'profile_form': profile_form})

@login_required(login_url='/login')
def my_password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password modificata con successo, è necessario riautenticarsi.")
            return redirect('/login/')
        else:
            messages.error(request, "qualcosa è andato storto durante la modifica; riprovare.")
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'multiplayer_chess/password_change.html', {'form': form})

@cache_control(no_cache=True)
@login_required(login_url='/login')
def lobby(request, mode):
    modes = ('classic', 'atomic', 'antichess', 'kingofthehill', 'threecheck', 'horde', 'racingkings')
    if mode not in modes:
        messages.error(request, "Variante non disponibile")
        return redirect('/home/')
    return render(request, "multiplayer_chess/lobby.html" , {'mode': mode})

@login_required(login_url='/login')
def cronologia(request):
    username = request.user
    cronologia1 = Game.objects.filter(player1=username)
    cronologia2 = Game.objects.filter(player2=username)
    cronologia = (cronologia1 | cronologia2)
    cro_filtrata = FilterCronologia(request.GET, queryset=cronologia)
    ctx = {'cronologia': cro_filtrata , 'username': username}
    return render(request, "multiplayer_chess/cronologia.html", ctx)

#-------------------------------------------------------------------------------------------------------------------------------------------
@cache_control(no_cache=True)
@login_required(login_url='/login')
def chess_game(request, room_number, variant):

    games = Game.objects.filter(room_id=room_number)
    game = games.first()
    user = request.user
    if game.player1 != user and game.player2 != user:
        messages.error(request, "Non fai parte di questa lobby")
        return redirect('/home/')
    if game.status == 'finished':
        messages.error(request, "La partita è terminata")
        return redirect('/home/')
    

    order = 1 if game.player1 == user else 2

    profiles1 = Profile.objects.filter(user_id=game.player1)
    profiles2 = Profile.objects.filter(user_id=game.player2)
    elo_player1 = 0
    elo_player2 = 0
    if order == 1:
        profile1 = profiles1.first()
        username1 = game.player1.username
        if variant == 'classic':
            elo_player1 = profile1.elo_classic
        elif variant == 'atomic':
            elo_player1 = profile1.elo_atomic
        elif variant == 'antichess':
            elo_player1 = profile1.elo_antichess

        profile2 = profiles2.first()
        username2 = game.player2.username
        if variant == 'classic':
            elo_player2 = profile2.elo_classic
        elif variant == 'atomic':
            elo_player2 = profile2.elo_atomic
        elif variant == 'antichess':
            elo_player2 = profile2.elo_antichess

    else:
        profile1 = profiles2.first()
        username1 = game.player2.username
        if variant == 'classic':
            elo_player1 = profile1.elo_classic
        elif variant == 'atomic':
            elo_player1 = profile1.elo_atomic
        elif variant == 'antichess':
            elo_player1 = profile1.elo_antichess

        profile2 = profiles1.first()
        username2 = game.player1.username
        if variant == 'classic':
            elo_player2 = profile2.elo_classic
        elif variant == 'atomic':
            elo_player2 = profile2.elo_atomic
        elif variant == 'antichess':
            elo_player2 = profile2.elo_antichess


    ctx = {
        "title" : "Partita scacchi",
        "order": order,
        "room_number": room_number,
        'username': username1,
        'user_image': profile1.photo,
        'user_elo1': elo_player1,
        'username2': username2,
        'user2_image': profile2.photo,
        'user_elo2': elo_player2,
        'variant': variant,
    }
    return render(request, template_name="multiplayer_chess/chess_game.html", context=ctx)


def get_position(request, variant, room_number):
    # Get the position here
    game = Game.objects.get(pk=room_number)
    fen = game.fen
    turn = game.turn
    position = {'fen': fen, 'turn':turn}
    response_data = json.dumps(position)
    return HttpResponse(response_data, content_type='application/json')


def tournament_list(request):
    all_tournaments = ChessTournament.objects.all()
    tournament_list = []
    for tournament in all_tournaments:
        tournament_dict = {
            'id': tournament.pk,
            'name': tournament.name,
            'start_date': tournament.start_date.isoformat(),
            'end_date': tournament.end_date.isoformat(),
            'players': tournament.players.count(),
            'variante': tournament.mode,
            'tier': tournament.tier
        }
        tournament_list.append(tournament_dict)
    return render(request, template_name="multiplayer_chess/tournament_list.html", context={'tournaments': tournament_list})


def tournament_details(request, tour_id):
    tournament = ChessTournament.objects.get(pk=tour_id)
    players = [player.user.username for player in tournament.players.all()]

    tournament_dict = {
        'id': tournament.pk,
        'name': tournament.name,
        'start_date': tournament.start_date.isoformat(),
        'end_date': tournament.end_date.isoformat(),
        'players': players
    }

    if request.user.username in players:
        iscritto = True
    else:
        iscritto = False
    print(iscritto)
    return render(request, template_name="multiplayer_chess/tournament_details.html", context={'tournament_data': tournament_dict , 'iscritto': iscritto})


def tournament_unsubscribe(request, tour_id):
    tournament = ChessTournament.objects.get(pk=tour_id)
    player = Profile.objects.get(user=request.user)
    tournament.players.remove(player)
    return redirect(reverse('multiplayer_chess:tournament_details', kwargs={'tour_id': tour_id}))

def tournament_subscribe(request, tour_id):
    tournament = ChessTournament.objects.get(pk=tour_id)
    player = Profile.objects.get(user=request.user)
    tournament.players.add(player)
    return redirect(reverse('multiplayer_chess:tournament_details', kwargs={'tour_id': tour_id}))

