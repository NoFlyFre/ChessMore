from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import *
from django.contrib.auth.decorators import login_required
from .models import *
from django.http import HttpResponse
import time
from django.views import View

# Create your views here.


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
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = LoginForm()
    return render(request=request, template_name="multiplayer_chess/login.html", context={"login_form": form})


def logoutView(request):
    logout(request)
    messages.success(request, "Logged out")
    return redirect("multiplayer_chess:login")


def registerView(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        try:
            user = form.save()
            Profile.objects.create(user=user)
            messages.success(request, "Registration successful, you can now log-in")
            return redirect("multiplayer_chess:login")
        except Exception as e:
            messages.error(request, str(e))
    form = RegisterForm()
    return render(request=request, template_name="multiplayer_chess/register.html", context={"register_form": form})

@login_required(login_url='/login')
def home(request):
    return render(request=request, template_name='multiplayer_chess/home.html')

@login_required(login_url='/login')
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        try:
            user_form.save()
            profile_form.save()
            messages.success(request, "profilo modificato con successo")
        except Exception as e:
            messages.error(request, str(e))
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
            messages.success(request, "Password modificata con successo, è necessario riautenticarsi")
            return redirect('/login/')
        else:
            messages.error(request, "La modifica non è riuscita.")
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'multiplayer_chess/password_change.html', {'form': form})


@login_required(login_url='/login')
def lobby(request, mode):
    return render(request, "multiplayer_chess/lobby.html" , {'mode': mode})
    


#-------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='/login')
def chess_game(request, room_number, variant):

    games = Game.objects.filter(room_id=room_number)
    game = games.first()
    user = request.user
    if game.player1 != user and game.player2 != user:
        return HttpResponse("Non fai parte di questa stanza")

    order = 1 if game.player1 == user else 2

    profiles1 = Profile.objects.filter(user_id=game.player1)
    profiles2 = Profile.objects.filter(user_id=game.player2)
    if order == 1:
        profile1 = profiles1.first()
        username1 = game.player1.username
        profile2 = profiles2.first()
        username2 = game.player2.username
    else:
        profile1 = profiles2.first()
        username1 = game.player2.username
        profile2 = profiles1.first()
        username2 = game.player1.username


    ctx = {
        "title" : "Partita scacchi",
        "order": order,
        "room_number": room_number,
        'username': username1,
        'user_image': profile1.photo,
        'username2': username2,
        'user2_image': profile2.photo,
        'variant': variant,
    }
    return render(request, template_name="multiplayer_chess/chess_game.html", context=ctx)
    