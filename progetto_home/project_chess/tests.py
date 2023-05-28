from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from multiplayer_chess.models import Game, Profile, User
from django.db.utils import IntegrityError
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from multiplayer_chess.forms import UserEditForm, AuthenticationForm, UserCreationForm, \
RegisterForm, ProfileEditForm, CustomPasswordChangeForm, LoginForm
from django.urls import reverse
from django.core.exceptions import ValidationError
from channels.testing import WebsocketCommunicator
from project_chess.consumers import Lobby
from asgiref.sync import sync_to_async
from multiplayer_chess.views import HOME_PATH, LOGIN_PATH
from . import game_logic

STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
TESTING_EMAIL_1 = 'testuser2@example.com'
TESTING_EMAIL_2 = 'mariorossi@test.com'
REGISTER_PATH = 'multiplayer_chess:register'
EDIT_PATH = 'multiplayer_chess:edit'
PASSWORD_CHANGE_PATH = 'multiplayer_chess:password_change'
LOBBY_PATH = 'multiplayer_chess:lobby'
CHESS_GAME_PATH = 'multiplayer_chess:chess_game'

def _create_user(username, password, email=None ):
    user = get_user_model().objects.create_user(
        username=username,
        password=password,
        email = email,
    )
    return user

def _create_game(player1, player2, room_id, mode, fen=STARTING_FEN, turn='w'):
    game = Game.objects.create(
        player1=player1,
        player2=player2,
        room_id=room_id,
        mode=mode,
        fen=fen,
        turn=turn,
    )
    return game

def _create_profile(user, date_of_birth=None, photo=None):
    profile = Profile.objects.create(
        user=user,
        date_of_birth=date_of_birth,
        photo=photo
    )
    return profile

def _create_photo():
    photo_data = b'photo data'
    photo_name = 'user.jpg'
    photo = SimpleUploadedFile(photo_name, photo_data, content_type='image/jpeg')
    return photo

def _create_non_authenticated_client():
    return Client()

def _create_authenticated_client(username, password):
    client = Client()
    user = _create_user(username=username, password=password)
    client.login(username=username, password=password)
    return (user, client)


def _create_register_form(username, email, password1, password2):
    form = RegisterForm(data = {
        'username': username,
        'email': email,
        'password1': password1,
        'password2': password2
    })
    return form

def _create_edituser_form(user, first_name, last_name, email):
    form = UserEditForm(instance=user, data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email
    })
    return form


def _create_editprofile_form(profile, date_of_birth, photo):
    form = ProfileEditForm(instance=profile, data = {
        'date_of_birth': date_of_birth,
        'photo': photo,
    })
    return form

def _create_changepassword_form(user, old_password, new_password1, new_password2):
    form = CustomPasswordChangeForm(user=user, data = {
        'old_password' : old_password,
        'new_password1': new_password1,
        'new_password2':new_password2
    })
    return form

def _create_socket_communicator_Lobby(user, mode):
    communicator = WebsocketCommunicator(Lobby.as_asgi(), f"/lobby/{mode}")
    communicator.scope['user'] = user
    communicator.scope['url_route'] = {'kwargs': {'mode': mode}}
    return communicator


####################################
##          test modelli          ##
####################################
class GameModelCreateTest(TestCase):

    def setUp(self):
        self.user1 = _create_user(username='user1',password='testpass123')
        self.user2 = _create_user(username='user2',password='testpass456')
        self.game1 = _create_game(self.user1, self.user2, room_id=1, mode='classic')
        self.game2 = _create_game(self.user1, self.user2, room_id=2, mode='atomic')


    def _test_game_model_attributes(self, game, room_id, mode, fen=STARTING_FEN, turn='w'):
        self.assertEqual(game.player1, self.user1)
        self.assertEqual(game.player2, self.user2)
        self.assertEqual(game.room_id, room_id)
        self.assertEqual(game.mode, mode)
        self.assertEqual(game.fen, fen)
        self.assertEqual(game.turn, turn)


    def test_game_model_attributes(self):
        self._test_game_model_attributes(self.game1, 1, 'classic')
        self._test_game_model_attributes(self.game2, 2, 'atomic')


    def test_game_model_queries(self):
        #get all games:
        all_games = Game.objects.all()
        self.assertIn(self.game1, all_games)
        self.assertIn(self.game2, all_games)

        #filter games by a specific mode
        classic_games = Game.objects.filter(mode='classic')
        atomic_games = Game.objects.filter(mode='atomic')
        self.assertEqual(len(classic_games), 1)
        self.assertEqual(classic_games[0], self.game1)
        self.assertEqual(len(atomic_games), 1)
        self.assertEqual(atomic_games[0], self.game2)

        #filter games by a specific user
        user1_games = Game.objects.filter(player1=self.user1)
        self.assertEqual(len(user1_games), 2)
        self.assertIn(self.game1, user1_games)
        self.assertIn(self.game2, user1_games)


    def test_game_model_validation(self):
        #test validazione con modalità non valida
        with self.assertRaises(ValidationError):
            _create_game(self.user1, self.user2, room_id=3, mode='non_esiste').full_clean()

        #test validazione con turno non valid
        with self.assertRaises(ValidationError):
            _create_game(self.user1, self.user2, room_id=4, mode='classic', turn='x').full_clean()

        #test valori di default
        game = Game.objects.create (
            player1=self.user1,
            player2=self.user2,
            room_id=5,
            mode='classic'
        )
        self.assertEqual(game.fen, STARTING_FEN)
        self.assertEqual(game.turn, 'w')


class UserAccountAndProfileCreateTests(TestCase):

    def setUp(self):
        self.user = _create_user(username='user1',password='testpass123', email='testemail@test.com')
        self.photo = _create_photo()
        self.profile = _create_profile(self.user, date(2001,10,10), self.photo)


    def test_user_profile_attributes(self):
        #user
        self.assertEqual(self.user.username, 'user1')
        self.assertEqual(self.user.email, 'testemail@test.com')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        #profile
        self.assertEqual(self.profile.user.username, 'user1')
        self.assertEqual(self.profile.date_of_birth, date(2001,10,10))
        today = date.today()
        expected_path = f"users/{today.year}/{str(today.month).zfill(2)}/{str(today.day).zfill(2)}/user.*\.jpg"
        self.assertRegex(self.profile.photo.name, expected_path)
        self.assertTrue(self.profile.photo.storage.path(self.profile.photo.name))

    def test_user_profile_validation(self):
        #unique username
        with self.assertRaises(IntegrityError):
            _create_user(username='user1',password='testpass321', email='email@test.com')


    def test_profile_method(self):
        self.assertEqual(self.profile.__str__(), f'Profile of {self.user.username}')

################################
##          test form         ##
################################

class TestLoginForm(TestCase):

    def setUp(self):
        self.user = _create_user(username='user1',password='testpass123')
        self.form = LoginForm(data = {
            'username': 'user1',
            'password': 'testpass123',
        })


    def test_login_form_validation(self):
        self.assertTrue(self.form.is_valid())
        form_non_valido = LoginForm(data = {
            'username': 'non_valido',
            'password': 'testpass123',
        })
        self.assertFalse(form_non_valido.is_valid())
        self.assertIn(
            'Please enter a correct username and password. Note that both fields may be case-sensitive.',
            form_non_valido.errors['__all__']
        )


    def test_login_form_attributes(self):
        self.assertIsInstance(self.form, AuthenticationForm)
        for visible in self.form.visible_fields():
            widget_classes = visible.field.widget.attrs.get('class', '')
            self.assertIn('form-control', widget_classes.split())
            self.assertIn('form-control-lg', widget_classes.split())
        self.form.is_valid()
        self.assertTrue(self.form.cleaned_data['username'], 'user1')
        self.assertTrue(self.form.cleaned_data['password'], 'testpass123')


    def test_login_form_submission(self):
        self.client_non_auth = _create_non_authenticated_client()
        self.form.is_valid()
        self.client_non_auth.post('/login/', data=self.form.cleaned_data)
        response = self.client_non_auth.get(reverse(HOME_PATH))
        self.assertEqual(response.status_code, 200)


class TestRegisterForm(TestCase):

    def setUp(self):
        _create_user('testuser','testpass123', 'testuser@test.com')
        self.form = _create_register_form('testuser2', TESTING_EMAIL_1 ,'testpass123','testpass123')


    def test_register_form_validation(self):
        self.assertTrue(self.form.is_valid())

        form_non_valido_email_vuota = _create_register_form('testuser3', None, 'testpass123','testpass123')
        self.assertFalse(form_non_valido_email_vuota.is_valid())
        self.assertIn(
            'This field is required.',
            form_non_valido_email_vuota.errors['email']
        )

        form_non_valido_email_in_uso = _create_register_form('testuser5','testuser@test.com','testpass123','testpass123')
        self.assertFalse(form_non_valido_email_in_uso.is_valid())
        self.assertIn(
            'questa e-mail è già registrata; riprovare.',
            form_non_valido_email_in_uso.errors['email']
        )

        form_non_valido_password_diverse = _create_register_form('testuser4','testuser4@example.com','testpass123','321ssaptset')
        self.assertFalse(form_non_valido_password_diverse.is_valid())
        self.assertIn(
            'The two password fields didn’t match.',
            form_non_valido_password_diverse.errors['password2']
        )


    def test_register_form_attributes(self):
        self.assertTrue(self.form, UserCreationForm)
        for visible in self.form.visible_fields():
            widget_classes = visible.field.widget.attrs.get('class', '')
            self.assertIn('form-control', widget_classes.split())
            self.assertIn('form-control-lg', widget_classes.split())
        self.assertEqual(self.form.Meta.model, User)
        self.assertEqual(self.form.Meta.fields, ["username", "email", "password1", "password2"])
        self.form.is_valid()
        self.assertEqual(self.form.cleaned_data['username'], 'testuser2')
        self.assertEqual(self.form.cleaned_data['email'], TESTING_EMAIL_1)
        self.assertEqual(self.form.cleaned_data['password1'], 'testpass123')
        self.assertEqual(self.form.cleaned_data['password2'], 'testpass123')


    def test_register_form_submission(self):
        user = self.form.save()
        self.assertEqual(user.username, 'testuser2')
        self.assertEqual(user.email, TESTING_EMAIL_1)


class UserEditFormTest(TestCase):

    def setUp(self):
        self.user = _create_user(username='user1',password='testpass123')
        self.form = _create_edituser_form(self.user,'Mario','Rossi', TESTING_EMAIL_2)


    def test_edituser_form_validation(self):
        self.assertTrue(self.form.is_valid())

        form_email_non_valida = _create_edituser_form(self.user, 'Mario','Rossi', 'email_non_valida')
        self.assertFalse(form_email_non_valida.is_valid())
        self.assertIn(
            'Enter a valid email address.',
            form_email_non_valida.errors['email']
        )


    def test_edituser_form_attributes(self):
        self.assertEqual(self.form.Meta.model, User)
        self.assertEqual(self.form.Meta.fields, ['first_name', 'last_name', 'email'])
        self.form.is_valid()
        self.assertEqual(self.form.cleaned_data['first_name'], 'Mario')
        self.assertEqual(self.form.cleaned_data['last_name'],'Rossi')
        self.assertEqual(self.form.cleaned_data['email'], TESTING_EMAIL_2)


    def test_edituser_form_submission(self):
        self.form.is_valid()
        self.form.save()
        self.assertEqual(self.user.first_name, 'Mario')
        self.assertEqual(self.user.last_name, 'Rossi')
        self.assertEqual(self.user.email, TESTING_EMAIL_2)


class ProfileEditFormTest(TestCase):

    def setUp(self):
        self.user = _create_user(username='user1',password='testpass123')
        self.profile = _create_profile(self.user)
        self.photo = _create_photo()
        self.form = _create_editprofile_form(self.profile, date(2001,10,10), self.photo)

    def test_editprofile_form_validation(self):
        self.assertTrue(self.form.is_valid())

        form_data_nascita_non_valida = _create_editprofile_form(self.profile, 'non_valida', self.photo)
        self.assertFalse(form_data_nascita_non_valida.is_valid())
        self.assertIn(
            'Enter a valid date.',
            form_data_nascita_non_valida.errors['date_of_birth']
        )

    def test_editprofile_form_attributes(self):
        self.assertEqual(self.form.Meta.model, Profile)
        self.assertEqual(self.form.Meta.fields, ['date_of_birth', 'photo'])
        self.form.is_valid()
        self.assertEqual(self.form.cleaned_data['date_of_birth'], date(2001,10,10))

    def test_editprofile_form_submission(self):
        self.form.is_valid()
        self.form.save()
        self.assertEqual(self.profile.date_of_birth, date(2001,10,10))


class CustomPasswordChangeFormTest(TestCase):

    def setUp(self):
        self.user = _create_user(username='user1',password='testpass123')
        self.form = _create_changepassword_form(self.user, 'testpass123', 'new_testpass123' , 'new_testpass123')

    def test_changepassword_form_validation(self):
        self.assertTrue(self.form.is_valid())
        form_with_wrong_old_psw = _create_changepassword_form(self.user, 'wrong', 'new_testpass123' , 'new_testpass123')
        self.assertFalse(form_with_wrong_old_psw.is_valid())
        self.assertIn(
            'Your old password was entered incorrectly. Please enter it again.',
            form_with_wrong_old_psw.errors['old_password']
        )
        form_with_wrong_mismatch_psw = _create_changepassword_form(self.user, 'testpass123', 'new_testpass123' , '321ssaptset_wen')
        self.assertIn(
            'The two password fields didn’t match.',
            form_with_wrong_mismatch_psw.errors['new_password2']
        )

    def test_changepassword_form_attributes(self):
        self.assertIsNone(self.form.fields['new_password1'].help_text)

    def test_changepassword_form_submission(self):
        hash_old_password = self.user.password
        self.form.is_valid()
        self.form.save()
        self.assertNotEqual(self.user.password, hash_old_password)


#################################
##          test views         ##
#################################

class ViewsTest(TestCase):

    def setUp(self):
        self.user, self.client_auth = _create_authenticated_client(username='testuser', password='testpass')
        self.client_non_auth = _create_non_authenticated_client()
        self.profile = _create_profile(self.user, date(2001,10,10), _create_photo())


    def test_index_view(self):
        #controlla che l'utente autenticato venga redirezionato alla home
        response = self.client_auth.get(reverse('multiplayer_chess:index'))
        self.assertRedirects(response, reverse(HOME_PATH), fetch_redirect_response=False)
        response = self.client_auth.get(response.url)
        self.assertEqual(response.status_code, 200)

        #controlla che l'utente autenticato venga redirezionato al login
        response = self.client_non_auth.get(reverse('multiplayer_chess:index'))
        self.assertRedirects(response, reverse(LOGIN_PATH), fetch_redirect_response=False)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 200)


    def test_login_view(self):
        response = self.client_non_auth.get(reverse(LOGIN_PATH))
        self.assertEqual(response.status_code, 200)

    def test_login_view_valid_credentials(self):
        response = self.client_non_auth.post(reverse(LOGIN_PATH), {'username': 'testuser', 'password': 'testpass'})
        self.assertRedirects(response, reverse(HOME_PATH), fetch_redirect_response=False)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 200)

    def test_login_view_invalid_credentials(self):
        response = self.client_non_auth.post(reverse(LOGIN_PATH), {'username': 'invaliduser', 'password': 'invalidpass'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "username o password errati; riprovare.")


    def test_logout_view(self):
        response = self.client_auth.get(reverse('multiplayer_chess:logout'))
        self.assertRedirects(response, reverse(LOGIN_PATH), fetch_redirect_response=False)
        response = self.client_auth.get(response.url)
        self.assertContains(response, "hai eseguito il log-out con successo.")
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client_auth.session)


    def test_register_view(self):
        response = self.client_auth.get(reverse(REGISTER_PATH))
        self.assertEqual(response.status_code, 200)

    def test_register_view_valid_form(self):
        response = self.client_non_auth.post(
            reverse(REGISTER_PATH),
            {'username': 'testusername2', 'email':'testemail2@email.com', 'password1': 'testpassword' , 'password2': 'testpassword'}
        )
        self.assertRedirects(response, reverse(LOGIN_PATH), fetch_redirect_response=False)
        redirect_url_register = response.url
        response = self.client_non_auth.get(redirect_url_register)
        self.assertContains(response, "registrazione avvenuta con successo; adesso, acceda al suo profilo.")
        response = self.client_non_auth.post(redirect_url_register, {'username': 'testusername2', 'password': 'testpassword'})
        self.assertRedirects(response, reverse(HOME_PATH), fetch_redirect_response=False)
        redirect_url_login = response.url
        response = self.client_non_auth.get(redirect_url_login)
        self.assertEqual(response.status_code, 200)

    def test_register_view_invalid_form(self):
        response = self.client_non_auth.post(
            reverse(REGISTER_PATH),
            {'username': 'testusername2', 'password1': 'testpassword' , 'password2': 'testpassword'}
        )
        self.assertContains(response, "qualcosa è andato storto durante la registrazione: This field is required.")
        self.assertEqual(response.status_code, 200)


    def test_home_view(self):
        #authenticated
        response = self.client_auth.get(reverse(HOME_PATH))
        self.assertEqual(response.status_code, 200)

        #non autenthicated
        response = self.client_non_auth.get(reverse(HOME_PATH))
        self.assertRedirects(response, '/login/', fetch_redirect_response=False)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 200)


    def test_edit_view(self):
        #authenticated
        response = self.client_auth.get(reverse(EDIT_PATH))
        self.assertEqual(response.status_code, 200)

        #non autenthicated
        response = self.client_non_auth.get(reverse(EDIT_PATH))
        self.assertRedirects(response, '/login?next=/edit/', fetch_redirect_response=False)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 301)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_view_correct_form(self):
        response = self.client_auth.post(reverse(EDIT_PATH), {
            'first_name': 'NuovoNome',
        })
        self.assertContains(response, 'profilo modificato con successo.')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NuovoNome')

    def test_edit_view_incorrect_form(self):
        response = self.client_auth.post(reverse(EDIT_PATH), {
            'email': 'non valida',
        })
        self.assertContains(response, "qualcosa è andato storto durante la modifica; riprovare.")
        self.assertEqual(response.status_code, 200)


    def test_password_change_view(self):
        #authenticated
        response = self.client_auth.get(reverse(PASSWORD_CHANGE_PATH))
        self.assertEqual(response.status_code, 200)

        #non autenthicated
        response = self.client_non_auth.get(reverse(PASSWORD_CHANGE_PATH))
        self.assertRedirects(response, '/login?next=/password-change/', fetch_redirect_response=False)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 301)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 200)

    def test_password_change_view_correct_form(self):
        response = self.client_auth.post( reverse(PASSWORD_CHANGE_PATH), {
            'old_password': 'testpass',
            'new_password1': 'testpass_nuova',
            'new_password2': 'testpass_nuova'
        })
        self.assertRedirects(response, reverse(LOGIN_PATH), fetch_redirect_response=False)
        redirect_url_login = response.url
        response = self.client_auth.get(redirect_url_login)
        self.assertContains(response, "Password modificata con successo, è necessario riautenticarsi.")
        self.assertEqual(response.status_code, 200)

    def test_password_change_view_incorrect_form(self):
        response = self.client_auth.post( reverse(PASSWORD_CHANGE_PATH), {
            'old_password': 'testpass',
            'new_password1': 'testpass_nuova',
            'new_password2': 'testpass_nuova2'
        })
        self.assertContains(response, "qualcosa è andato storto durante la modifica; riprovare.")
        self.assertEqual(response.status_code, 200)


    def test_lobby_view(self):
        #authenticated
        response = self.client_auth.get(reverse(LOBBY_PATH, args=('classic',)))
        self.assertEqual(response.status_code, 200)
        response = self.client_auth.get(reverse(LOBBY_PATH, args=('atomic',)))
        self.assertEqual(response.status_code, 200)
        response = self.client_auth.get(reverse(LOBBY_PATH, args=('qdwwdqwqdwqd',)))
        self.assertRedirects(response, reverse(HOME_PATH), fetch_redirect_response=False)
        redirect_url_home = response.url
        response = self.client_auth.get(redirect_url_home)
        self.assertContains(response, "Variante non disponibile")
        self.assertEqual(response.status_code, 200)

        #non authenticated
        response = self.client_non_auth.get(reverse(LOBBY_PATH, args=('classic',)))
        self.assertRedirects(response, '/login?next=/lobby/classic/', fetch_redirect_response=False)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 301)
        response = self.client_non_auth.get(response.url)
        self.assertEqual(response.status_code, 200)


class GameTest(TestCase):

    def setUp(self):
        self.user1, self.client_auth_user1 = _create_authenticated_client(username="provauser1", password="passwordprova1")
        self.profile1 = _create_profile(user=self.user1)

        self.user2, self.client_auth_user2 = _create_authenticated_client(username="provauser2", password="passwordprova2")
        self.profile2 = _create_profile(user=self.user2)

        self.user3, self.client_auth_user3 = _create_authenticated_client(username="provauser3", password="passwordprova3")
        self.profile3 = _create_profile(user=self.user3)

        self.game = _create_game(self.user1, self.user2, 1 ,'classic')


    def test_chess_game_view(self):
        #giocatori della partita
        response = self.client_auth_user1.get(reverse(CHESS_GAME_PATH, args=('classic', '1')))
        self.assertEqual(response.status_code, 200)
        response = self.client_auth_user2.get(reverse(CHESS_GAME_PATH, args=('classic', '1')))
        self.assertEqual(response.status_code, 200)
        #giocatori non della partita
        response = self.client_auth_user3.get(reverse(CHESS_GAME_PATH, args=('classic', '1')))
        self.assertRedirects(response, reverse(HOME_PATH), fetch_redirect_response=False)
        response = self.client_auth_user3.get(response.url)
        self.assertContains(response, "Non fai parte di questa lobby")
        self.assertEqual(response.status_code, 200)


    def test_get_position_view(self):
        response = self.client.get(reverse('multiplayer_chess:get_position', args=('classic', '1')))
        self.assertContains(response, STARTING_FEN)
        self.assertEqual(response.status_code, 200)

        _create_game(self.user1, self.user2, 2 ,'classic', fen='prova')
        response = self.client.get(reverse('multiplayer_chess:get_position', args=('classic', '2')))
        self.assertContains(response, 'prova')
        self.assertEqual(response.status_code, 200)

#self.assertTemplateUsed(response, 'multiplayer_chess/chess_game.html')

####################################
##          test consumers        ##
####################################

class MyLobbyTestCase(TestCase):

    def setUp(self):
        self.user1, self.client_auth_user1 = _create_authenticated_client(username="provauser1", password="passwordprova1")
        self.user2, self.client_auth_user2 = _create_authenticated_client(username="provauser2", password="passwordprova2")
        _create_profile(self.user1)
        _create_profile(self.user2)
        _create_game( self.user1, self.user2, 1 ,'classic')

    #controlla che nel DB sia presente una sola partita modalità classica con player2 non impostato
    def _check_game_exists(self, mode):
        partite_create = Game.objects.filter(player2__isnull=True, mode=mode)
        self.assertEqual(partite_create.count(), 1)
        partita = partite_create.first()
        self.assertEqual(partita.player1, self.user1)

    def _check_game_not_exists(self, mode):
        self.assertEqual(Game.objects.filter(player2__isnull=True, mode=mode).count(), 0)

    async def _check_connection(self, communicator):
        connected, _ = await communicator.connect()
        assert connected

    async def _test_one_user(self, mode):
        #3 pagine aperte di uno stesso utente non devo creare più partite ne farne partire una
        communicator1 = _create_socket_communicator_Lobby(self.user1, mode)
        await self._check_connection(communicator1)
        self.assertEqual(len(Lobby.connected_users), 1)
        self.assertTrue(Lobby.firstConnection[mode])

        communicator2 = _create_socket_communicator_Lobby(self.user1, mode)
        await self._check_connection(communicator2)
        self.assertEqual(len(Lobby.connected_users), 2)
        self.assertFalse(Lobby.firstConnection[mode])

        communicator3 = _create_socket_communicator_Lobby(self.user1, mode)
        await self._check_connection(communicator3)
        self.assertEqual(len(Lobby.connected_users), 3)
        self.assertFalse(Lobby.firstConnection[mode])

        await sync_to_async(self._check_game_exists)(mode)

        #se l'utente si disconnette con 2 pagine su 3, la partita non deve essere cancellata
        await communicator3.disconnect()
        self.assertEqual(len(Lobby.connected_users), 2)
        self.assertFalse(Lobby.lastConnection[mode])

        await sync_to_async(self._check_game_exists)(mode)

        await communicator2.disconnect()
        self.assertEqual(len(Lobby.connected_users), 1)
        self.assertFalse(Lobby.lastConnection[mode])

        await sync_to_async(self._check_game_exists)(mode)

        #se l'utente di disconnette con tutte le pagine, la partita deve essere cancellata
        await communicator1.disconnect()
        self.assertEqual(len(Lobby.connected_users), 0)
        self.assertTrue(Lobby.lastConnection[mode])

        await sync_to_async(self._check_game_not_exists)(mode)


    async def test_one_user(self):
        await self._test_one_user('classic')
        await self._test_one_user('atomic')

    def _check_game_has_both_players(self, mode):
        games = Game.objects.filter(player1=self.user1, player2=self.user2, mode=mode)
        #1 appena creato e 1 di default ( game_id è scelto come (max tra tutti i game_id nel DB) + 1, se non c'è nessun elemento dà errore)
        if mode == 'classic':
            self.assertEqual(games.count(), 2)
        else:
            self.assertEqual(games.count(), 1)


    async def _test_two_users(self, mode):

        communicator_user1 = _create_socket_communicator_Lobby(self.user1, mode)
        await self._check_connection(communicator_user1)
        await sync_to_async(self._check_game_exists)(mode)

        communicator_user2 = _create_socket_communicator_Lobby(self.user2, mode)
        await self._check_connection(communicator_user2)
        await sync_to_async(self._check_game_has_both_players)(mode)

    async def test_two_users(self):
        await self._test_two_users('classic')
        await self._test_two_users('atomic')

#######################################
##          modulo game logic        ##
#######################################

class TestGameLogic(TestCase):

    def test_new_game_standard_board(self):
        id = 1
        variant = "standard"
        parametro_fen = None

        game_logic.new_game(id, variant, parametro_fen)
        assert isinstance(game_logic.games[id], game_logic.chess.Board), "game must be an instance of chess.Board"

    def test_new_game_atomic_board(self):
        id = 2
        variant = "atomic"
        parametro_fen = None

        game_logic.new_game(id, variant, parametro_fen)
        assert isinstance(game_logic.games[id], game_logic.chess.variant.AtomicBoard), "game must be an instance of AtomicBoard"

    def test_new_game_antichess_board(self):
        id = 3
        variant = "antichess"
        parametro_fen = None

        game_logic.new_game(id, variant, parametro_fen)
        assert isinstance(game_logic.games[id], game_logic.chess.variant.AntichessBoard), "game must be an instance of AtomicBoard"
    

    def test_new_game_king_of_the_hill_board(self):
        id = 4
        variant = "kingofthehill"
        parametro_fen = None

        game_logic.new_game(id, variant, parametro_fen)
        assert isinstance(game_logic.games[id], game_logic.chess.variant.KingOfTheHillBoard), "game must be an instance of KingOfTheHillBoard"


    def test_new_game_three_check_board(self):
        id = 5
        variant = "threecheck"
        parametro_fen = None

        game_logic.new_game(id, variant, parametro_fen)
        assert isinstance(game_logic.games[id], game_logic.chess.variant.ThreeCheckBoard), "game must be an instance of ThreeCheckBoard"


    def test_new_game_horde_board(self):
        id = 6
        variant = "horde"
        parametro_fen = None

        game_logic.new_game(id, variant, parametro_fen)
        assert isinstance(game_logic.games[id], game_logic.chess.variant.HordeBoard), "game must be an instance of HordeBoard"


    def test_new_racing_kings_board(self):
        id = 7
        variant = "racingkings"
        parametro_fen = None

        game_logic.new_game(id, variant, parametro_fen)
        assert isinstance(game_logic.games[id], game_logic.chess.variant.RacingKingsBoard), "game must be an instance of RacingKingsBoard"

    def test_insert_move(self):
        game_logic.new_game(1, "standard", game_logic.chess.STARTING_FEN)
        
        result = game_logic.insert_move(1, "e2e4")
        assert result == "success"
        assert game_logic.games[1].fen() == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        
        result = game_logic.insert_move(1, "invalidmove")
        assert result == "error"
        assert game_logic.games[1].fen() == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


    def test_status(self):
        # crea una partita in stato scacco-matto
        game_logic.new_game(1, "standard", "rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        assert game_logic.status(1) == "checkmate"
        
        # crea una partita in stato stale-mate
        game_logic.new_game(2, "standard", "8/8/2q5/k3K3/6q1/8/2r2n2/7r w - - 28 53")
        assert game_logic.status(2) == "stalemate"
        
        # crea una partita in stato di pareggio per una variante
        game_logic.new_game(4, "atomic", "rn4nr/pp4pp/8/8/8/3p4/PP3PPP/RNB1KBNR b KQ - 0 9")
        assert game_logic.status(4) == "var_loss"

        # crea una partita in stato ongoing, ossia ancora in corso
        game_logic.new_game(5, "standard", game_logic.chess.STARTING_FEN)
        assert game_logic.status(5) is None

    def test_turn(self):

        game_logic.new_game(1, "standard" , game_logic.chess.STARTING_FEN)
        self.assertEqual(game_logic.turn(1), "w")

        # fai una mossa con il bianco
        game_logic.insert_move(1, "e2e4")

        # fai una mossa con il nero
        self.assertEqual(game_logic.turn(1), "b")
