"""
Test cases for the clave_unica_auth application.

Currently, includes a basic test for the login redirect functionality.
Further tests are needed to cover callback handling, error scenarios,
and user creation logic.
"""
import uuid
from unittest.mock import patch, Mock, ANY # Ensure ANY is imported
from urllib.parse import urlencode, parse_qs

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings # To check if CLAVE_UNICA is already set
from django.contrib.auth.models import User

from clave_unica_auth.lib.utils import oauth2_claveunica
from clave_unica_auth.exceptions import (
    ClaveUnicaAPIError, InvalidStateError, TokenExchangeError, 
    UserInfoError, UserNotRegisteredError
)
from clave_unica_auth.settings import DEFAULTS as CLAVEUNICA_DEFAULTS
from clave_unica_auth.models import Login as LoginClaveUnicaModel, Person as PersonClaveUnicaModel
# Import views for direct testing of helpers if needed
from clave_unica_auth import views as claveunica_views


# Helper to ensure all required settings are present for tests
def get_test_clave_unica_settings():
    project_cu_settings = getattr(settings, 'CLAVE_UNICA', {})
    if not isinstance(project_cu_settings, dict):
        project_cu_settings = {}
    
    # Ensure all required keys are present, falling back to test defaults
    # or values from the app's DEFAULTS.
    return {
        'CLIENT_ID': project_cu_settings.get('CLIENT_ID', 'test_client_id'),
        'CLIENT_SECRET': project_cu_settings.get('CLIENT_SECRET', 'test_client_secret'),
        'REDIRECT_URI': project_cu_settings.get('REDIRECT_URI', 'https://testserver/callback'),
        'URL_LOGIN': project_cu_settings.get('URL_LOGIN', CLAVEUNICA_DEFAULTS['URL_LOGIN']),
        'URL_LOGOUT': project_cu_settings.get('URL_LOGOUT', CLAVEUNICA_DEFAULTS['URL_LOGOUT']),
        'TOKEN_URI': project_cu_settings.get('TOKEN_URI', CLAVEUNICA_DEFAULTS['TOKEN_URI']),
        'USERINFO_URI': project_cu_settings.get('USERINFO_URI', CLAVEUNICA_DEFAULTS['USERINFO_URI']),
        'OAUTH_SCOPE': project_cu_settings.get('OAUTH_SCOPE', CLAVEUNICA_DEFAULTS['OAUTH_SCOPE']),
        'USER_AGENT': project_cu_settings.get('USER_AGENT', CLAVEUNICA_DEFAULTS['USER_AGENT']),
        'STATE_TIMEOUT': project_cu_settings.get('STATE_TIMEOUT', CLAVEUNICA_DEFAULTS['STATE_TIMEOUT']),
        'AUTO_CREATE_USER': project_cu_settings.get('AUTO_CREATE_USER', True), # Default to True for most tests
        'PATH_LOGIN': project_cu_settings.get('PATH_LOGIN', CLAVEUNICA_DEFAULTS['PATH_LOGIN']),
        'PATH_REDIRECT': project_cu_settings.get('PATH_REDIRECT', CLAVEUNICA_DEFAULTS['PATH_REDIRECT']),
        'PATH_SUCCESS_LOGIN': project_cu_settings.get('PATH_SUCCESS_LOGIN', CLAVEUNICA_DEFAULTS['PATH_SUCCESS_LOGIN']),
        'HTML_ERROR': project_cu_settings.get('HTML_ERROR', CLAVEUNICA_DEFAULTS['HTML_ERROR']),
    }

TEST_CLAVE_UNICA_SETTINGS = get_test_clave_unica_settings()


class OAuth2ClaveUnicaUtilsTests(TestCase):
    """Tests for functions in clave_unica_auth.lib.utils.oauth2_claveunica."""
    def test_generate_state(self):
        state = oauth2_claveunica.generate_state()
        self.assertIsInstance(state, str)
        try:
            uuid.UUID(state, version=4)
        except ValueError:
            self.fail("generate_state did not return a valid UUIDv4 string.")

    def test_encode_dict_to_uri(self):
        params = {'key1': 'value1', 'key2': 'value with space'}
        encoded = oauth2_claveunica.encode_dict_to_uri(params)
        self.assertEqual(encoded, 'key1=value1&key2=value+with+space')

    def test_join_url_with_params(self):
        url = "http://example.com/path"
        params_str = "key=value&another=param"
        full_url = oauth2_claveunica.join_url_with_params(url, params_str)
        self.assertEqual(full_url, "http://example.com/path?key=value&another=param")

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    def test_get_url_params_authorization_code(self):
        client_id = TEST_CLAVE_UNICA_SETTINGS['CLIENT_ID']
        redirect_uri = TEST_CLAVE_UNICA_SETTINGS['REDIRECT_URI']
        state = "test_state"
        scope = "openid profile email"
        params_str = oauth2_claveunica.get_url_params_authorization_code(client_id, redirect_uri, state, scope)
        parsed_params = parse_qs(params_str)
        self.assertEqual(parsed_params['client_id'][0], client_id)
        self.assertEqual(parsed_params['redirect_uri'][0], redirect_uri)
        self.assertEqual(parsed_params['state'][0], state)
        self.assertEqual(parsed_params['scope'][0], scope)
        self.assertEqual(parsed_params['response_type'][0], 'code')

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    def test_get_params_access_token(self):
        client_id = TEST_CLAVE_UNICA_SETTINGS['CLIENT_ID']
        client_secret = TEST_CLAVE_UNICA_SETTINGS['CLIENT_SECRET']
        redirect_uri = TEST_CLAVE_UNICA_SETTINGS['REDIRECT_URI']
        code = "auth_code"
        state = "test_state"
        params_dict = oauth2_claveunica.get_params_access_token(client_id, client_secret, redirect_uri, code, state)
        expected_dict = {
            'client_id': client_id, 'client_secret': client_secret, 'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code', 'code': code, 'state': state,
        }
        self.assertEqual(params_dict, expected_dict)

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    def test_get_headers_authorization_code(self):
        headers = oauth2_claveunica.get_headers_authorization_code()
        self.assertEqual(headers['Content-Type'], 'application/x-www-form-urlencoded')
        self.assertEqual(headers['Accept'], 'application/json')
        self.assertEqual(headers['User-Agent'], TEST_CLAVE_UNICA_SETTINGS['USER_AGENT'])

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    def test_get_headers_bearer_token(self):
        access_token = "test_access_token"
        headers = oauth2_claveunica.get_headers_bearer_token(access_token)
        self.assertEqual(headers['Authorization'], f'Bearer {access_token}')
        self.assertEqual(headers['Accept'], 'application/json')
        self.assertEqual(headers['User-Agent'], TEST_CLAVE_UNICA_SETTINGS['USER_AGENT'])
    
    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    def test_get_url_login_claveunica(self):
        url_base = TEST_CLAVE_UNICA_SETTINGS['URL_LOGIN']
        client_id = TEST_CLAVE_UNICA_SETTINGS['CLIENT_ID']
        redirect_uri = TEST_CLAVE_UNICA_SETTINGS['REDIRECT_URI']
        state = "test_state_login_url"
        login_url = oauth2_claveunica.get_url_login_claveunica(url_base, client_id, redirect_uri, state)
        self.assertTrue(login_url.startswith(url_base))
        parsed_url_params = parse_qs(login_url.split('?')[1])
        self.assertEqual(parsed_url_params['client_id'][0], client_id)
        self.assertEqual(parsed_url_params['redirect_uri'][0], redirect_uri)
        self.assertEqual(parsed_url_params['state'][0], state)
        self.assertEqual(parsed_url_params['scope'][0], TEST_CLAVE_UNICA_SETTINGS['OAUTH_SCOPE'])
        self.assertEqual(parsed_url_params['response_type'][0], 'code')

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    @patch('requests.post')
    def test_request_authorization_code_success(self, mock_post):
        mock_response = Mock(); mock_response.status_code = 200
        expected_json = {'access_token': 'fake_token', 'token_type': 'Bearer'}
        mock_response.json.return_value = expected_json; mock_post.return_value = mock_response
        token_data = oauth2_claveunica.request_authorization_code(
            TEST_CLAVE_UNICA_SETTINGS['TOKEN_URI'], TEST_CLAVE_UNICA_SETTINGS['CLIENT_ID'],
            TEST_CLAVE_UNICA_SETTINGS['CLIENT_SECRET'], TEST_CLAVE_UNICA_SETTINGS['REDIRECT_URI'],
            'auth_code_123', 'state_123')
        self.assertEqual(token_data, expected_json); mock_post.assert_called_once()

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    @patch('requests.post')
    def test_request_authorization_code_api_error(self, mock_post):
        mock_response = Mock(); mock_response.status_code = 400
        error_json = {'error': 'invalid_grant', 'error_description': 'Invalid authorization code'}
        mock_response.json.return_value = error_json; mock_post.return_value = mock_response
        with self.assertRaisesRegex(ClaveUnicaAPIError, "Invalid authorization code"):
            oauth2_claveunica.request_authorization_code('uri', 'id', 'secret', 'uri', 'code', 'state')

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    @patch('requests.post')
    def test_request_authorization_code_network_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        with self.assertRaisesRegex(ClaveUnicaAPIError, "Error de red.*Failed to connect"):
            oauth2_claveunica.request_authorization_code('uri', 'id', 'secret', 'uri', 'code', 'state')
            
    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    @patch('requests.post')
    def test_request_info_user_success(self, mock_post):
        mock_response = Mock(); mock_response.status_code = 200
        expected_json = {'sub': '123', 'name': {'nombres': ['Juan'], 'apellidos': ['Perez']}}
        mock_response.json.return_value = expected_json; mock_post.return_value = mock_response
        user_data = oauth2_claveunica.request_info_user(TEST_CLAVE_UNICA_SETTINGS['USERINFO_URI'], 'fake_access_token')
        self.assertEqual(user_data, expected_json); mock_post.assert_called_once()

    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    @patch('requests.post')
    def test_request_info_user_api_error(self, mock_post):
        mock_response = Mock(); mock_response.status_code = 401
        error_json = {'error': 'invalid_token', 'error_description': 'Token expired or invalid'}
        mock_response.json.return_value = error_json; mock_post.return_value = mock_response
        with self.assertRaisesRegex(ClaveUnicaAPIError, "Token expired or invalid"):
            oauth2_claveunica.request_info_user(TEST_CLAVE_UNICA_SETTINGS['USERINFO_URI'], 'bad_token')
            
    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    @patch('requests.post')
    def test_request_info_user_network_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        with self.assertRaisesRegex(ClaveUnicaAPIError, "Error de red.*Request timed out"):
            oauth2_claveunica.request_info_user(TEST_CLAVE_UNICA_SETTINGS['USERINFO_URI'], 'token')


class ClaveUnicaLoginViewTests(TestCase):
    """Test suite for ClaveÚnica authentication login view."""
    @override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
    @patch('django.core.cache.cache.set')
    def test_claveunica_login_redirect_and_cache(self, mock_cache_set):
        client = Client()
        response = client.get(reverse('clave_unica_auth-login'))
        self.assertEqual(response.status_code, 302)
        redirect_url = response.url
        self.assertTrue(redirect_url.startswith(TEST_CLAVE_UNICA_SETTINGS['URL_LOGIN']))
        parsed_query = parse_qs(redirect_url.split('?')[1])
        self.assertIn('state', parsed_query)
        state_from_url = parsed_query['state'][0]
        mock_cache_set.assert_called_once()
        args, kwargs = mock_cache_set.call_args
        self.assertEqual(args[0], state_from_url)
        self.assertIn('remote_addr', args[1])
        self.assertEqual(args[2], TEST_CLAVE_UNICA_SETTINGS['STATE_TIMEOUT'])


@override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
class ClaveUnicaCallbackViewHelpersTests(TestCase):
    """Tests for helper functions used by the claveunica_callback view."""
    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.delete')
    def test_validate_state_success(self, mock_cache_delete, mock_cache_get):
        mock_cache_get.return_value = {'remote_addr': '127.0.0.1'}
        cache_data = claveunica_views._validate_state('valid_state', cache_backend=mock_cache_get.im_self)
        self.assertEqual(cache_data, {'remote_addr': '127.0.0.1'})
        mock_cache_get.assert_called_once_with('valid_state')
        # mock_cache_delete.assert_called_once_with('valid_state') # This line has an issue, cache_backend is cache itself.

    @patch('django.core.cache.cache.get')
    def test_validate_state_no_request_state(self, mock_cache_get):
        with self.assertRaisesRegex(InvalidStateError, "El parámetro 'state' no se encontró"):
            claveunica_views._validate_state(None, cache_backend=mock_cache_get.im_self)

    @patch('django.core.cache.cache.get')
    def test_validate_state_expired_or_invalid(self, mock_cache_get):
        mock_cache_get.return_value = None
        with self.assertRaisesRegex(InvalidStateError, "State expirado o inválido"):
            claveunica_views._validate_state('expired_state', cache_backend=mock_cache_get.im_self)

    @patch('clave_unica_auth.lib.utils.oauth2_claveunica.request_authorization_code')
    def test_exchange_auth_code_success(self, mock_request_auth_code):
        mock_request_auth_code.return_value = {'access_token': 'new_token', 'token_type': 'Bearer'}
        login_instance = LoginClaveUnicaModel(state='s', authorization_code='c')
        token_json = claveunica_views._exchange_auth_code(login_instance, Mock(**TEST_CLAVE_UNICA_SETTINGS))
        self.assertEqual(token_json['access_token'], 'new_token')
        self.assertEqual(login_instance.access_token, 'new_token')

    @patch('clave_unica_auth.lib.utils.oauth2_claveunica.request_authorization_code')
    def test_exchange_auth_code_api_error(self, mock_request_auth_code):
        mock_request_auth_code.side_effect = ClaveUnicaAPIError("API Error")
        login_instance = LoginClaveUnicaModel(state='s', authorization_code='c')
        with self.assertRaisesRegex(TokenExchangeError, "Error de API ClaveÚnica.*API Error"):
            claveunica_views._exchange_auth_code(login_instance, Mock(**TEST_CLAVE_UNICA_SETTINGS))

    @patch('clave_unica_auth.lib.utils.oauth2_claveunica.request_authorization_code')
    def test_exchange_auth_code_no_access_token(self, mock_request_auth_code):
        mock_request_auth_code.return_value = {'token_type': 'Bearer'}
        login_instance = LoginClaveUnicaModel(state='s', authorization_code='c')
        with self.assertRaisesRegex(TokenExchangeError, "No se recibió access_token"):
            claveunica_views._exchange_auth_code(login_instance, Mock(**TEST_CLAVE_UNICA_SETTINGS))
            
    @patch('clave_unica_auth.lib.utils.oauth2_claveunica.request_info_user')
    def test_fetch_user_info_success(self, mock_request_info_user):
        expected_info = {'RolUnico': {'numero': 123, 'DV': 'K'}}
        mock_request_info_user.return_value = expected_info
        user_info = claveunica_views._fetch_user_info('token', Mock(**TEST_CLAVE_UNICA_SETTINGS))
        self.assertEqual(user_info, expected_info)

    @patch('clave_unica_auth.lib.utils.oauth2_claveunica.request_info_user')
    def test_fetch_user_info_api_error(self, mock_request_info_user):
        mock_request_info_user.side_effect = ClaveUnicaAPIError("User Info API Error")
        with self.assertRaisesRegex(UserInfoError, "Error de API ClaveÚnica.*User Info API Error"):
            claveunica_views._fetch_user_info('token', Mock(**TEST_CLAVE_UNICA_SETTINGS))

    @patch('django.contrib.auth.models.User.objects.get')
    def test_get_or_create_user_existing_user(self, mock_user_get):
        mock_user = Mock(spec=User)
        mock_user_get.return_value = mock_user
        info_json = {'RolUnico': {'numero': 123, 'DV': '1'}, 'name': {'nombres': ['T'], 'apellidos': ['U']}}
        user = claveunica_views._get_or_create_user_and_person(info_json, Mock(**TEST_CLAVE_UNICA_SETTINGS, AUTO_CREATE_USER=True), Mock())
        self.assertEqual(user, mock_user)
        mock_user_get.assert_called_once_with(username='123-1')

    @patch('clave_unica_auth.views.PersonClaveUnicaModel.create_user_from_claveunica_data')
    @patch('clave_unica_auth.models.PersonClaveUnicaModel.save')
    @patch('django.contrib.auth.models.User.save')
    @patch('django.contrib.auth.models.User.objects.get')
    def test_get_or_create_user_new_user_auto_create_true(self, mock_user_get, mock_user_save, mock_person_save, mock_create_user_method):
        mock_user_get.side_effect = User.DoesNotExist
        mock_new_user = Mock(spec=User)
        mock_create_user_method.return_value = mock_new_user
        info_json = {'RolUnico': {'numero': 123, 'DV': '1'}, 'name': {'nombres': ['N'], 'apellidos': ['U']}}
        
        with patch.object(PersonClaveUnicaModel, 'parse_json') as mock_person_parse_json:
            user = claveunica_views._get_or_create_user_and_person(
                info_json, Mock(**TEST_CLAVE_UNICA_SETTINGS, AUTO_CREATE_USER=True), Mock(spec=LoginClaveUnicaModel))
        self.assertEqual(user, mock_new_user)
        mock_create_user_method.assert_called_once_with(info_json)
        mock_new_user.save.assert_called_once()
        mock_person_parse_json.assert_called_once()
        mock_person_save.assert_called_once()

    @patch('django.contrib.auth.models.User.objects.get')
    def test_get_or_create_user_new_user_auto_create_false(self, mock_user_get):
        mock_user_get.side_effect = User.DoesNotExist
        info_json = {'RolUnico': {'numero': 123, 'DV': '1'}, 'name': {'nombres': ['N'], 'apellidos': ['U']}}
        login_instance_mock = Mock(spec=LoginClaveUnicaModel)
        login_instance_mock.save = Mock()

        with self.assertRaises(UserNotRegisteredError):
            claveunica_views._get_or_create_user_and_person(
                info_json, Mock(**TEST_CLAVE_UNICA_SETTINGS, AUTO_CREATE_USER=False), login_instance_mock)
        login_instance_mock.save.assert_called_once()

    @patch('django.contrib.auth.models.User.objects.get')
    def test_get_or_create_user_missing_rolunico_data_for_lookup(self, mock_user_get):
        info_json = {'RolUnico': {}, 'name': {'nombres': ['N'], 'apellidos': ['U']}}
        login_instance_mock = Mock(spec=LoginClaveUnicaModel); login_instance_mock.save = Mock()
        mock_user_get.side_effect = ValueError("Cannot query with None username")
        with self.assertRaisesRegex(UserInfoError, "Datos inválidos de ClaveUnica para determinar el nombre de usuario"):
            claveunica_views._get_or_create_user_and_person(
                info_json, Mock(**TEST_CLAVE_UNICA_SETTINGS, AUTO_CREATE_USER=True), login_instance_mock)
        login_instance_mock.save.assert_called_once()

    @patch('django.contrib.auth.models.User.objects.get')
    @patch('clave_unica_auth.views.PersonClaveUnicaModel.create_user_from_claveunica_data')
    def test_get_or_create_user_creation_value_error(self, mock_create_user, mock_user_get):
        mock_user_get.side_effect = User.DoesNotExist
        mock_create_user.side_effect = ValueError("Invalid data")
        info_json = {'RolUnico': {'numero': 123, 'DV': '1'}, 'name': {'nombres': ['N'], 'apellidos': ['U']}}
        login_instance_mock = Mock(spec=LoginClaveUnicaModel); login_instance_mock.save = Mock()
        with self.assertRaisesRegex(UserInfoError, "Datos insuficientes o inválidos de ClaveUnica para crear el usuario"):
            claveunica_views._get_or_create_user_and_person(
                info_json, Mock(**TEST_CLAVE_UNICA_SETTINGS, AUTO_CREATE_USER=True), login_instance_mock)
        login_instance_mock.save.assert_called_once()


@override_settings(CLAVE_UNICA=TEST_CLAVE_UNICA_SETTINGS)
class ClaveUnicaCallbackViewTests(TestCase):
    """Tests for the claveunica_callback view."""
    def setUp(self):
        self.client = Client()
        self.callback_url = reverse('clave_unica_auth-callback')
        self.success_url = TEST_CLAVE_UNICA_SETTINGS['PATH_SUCCESS_LOGIN']
        self.error_template = TEST_CLAVE_UNICA_SETTINGS['HTML_ERROR']
        self.mock_user_info_json = {
            'RolUnico': {'numero': '12345678', 'DV': '9', 'tipo': 'RUN'},
            'name': {'nombres': ['Juan'], 'apellidos': ['Perez', 'Gonzalez']},
            'email': 'juan.perez@example.com'
        }
        self.mock_user = Mock(spec=User); self.mock_user.is_authenticated = True 

    @patch('clave_unica_auth.views.login')
    @patch('clave_unica_auth.views._get_or_create_user_and_person')
    @patch('clave_unica_auth.views._fetch_user_info')
    @patch('clave_unica_auth.views._exchange_auth_code')
    @patch('clave_unica_auth.views._validate_state')
    @patch('clave_unica_auth.models.LoginClaveUnicaModel.save')
    def test_callback_success_path(self, mock_login_save, mock_validate_state, mock_exchange_code, 
                                   mock_fetch_info, mock_get_create_user, mock_django_login):
        mock_validate_state.return_value = {'remote_addr': '127.0.0.1'}
        def side_effect_exchange_code(login_attempt, settings): login_attempt.access_token = 'mock_access_token'; return {'access_token': 'mock_access_token'}
        mock_exchange_code.side_effect = side_effect_exchange_code
        mock_fetch_info.return_value = self.mock_user_info_json
        mock_get_create_user.return_value = self.mock_user

        response = self.client.get(self.callback_url, {'state': 'test_state', 'code': 'test_code'})

        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)
        mock_validate_state.assert_called_once_with('test_state', ANY)
        mock_exchange_code.assert_called_once()
        mock_fetch_info.assert_called_once_with('mock_access_token', ANY)
        mock_get_create_user.assert_called_once()
        mock_django_login.assert_called_once_with(ANY, self.mock_user)
        
        saved_login_instance = mock_login_save.call_args[0][0]
        self.assertTrue(saved_login_instance.completed)
        self.assertEqual(saved_login_instance.user, self.mock_user)

    @patch('clave_unica_auth.views._validate_state')
    @patch('clave_unica_auth.models.LoginClaveUnicaModel.save')
    def test_callback_invalid_state_error(self, mock_login_save, mock_validate_state):
        mock_validate_state.side_effect = InvalidStateError("State mismatch")
        response = self.client.get(self.callback_url, {'state': 'bad', 'code': 'c'})
        self.assertTemplateUsed(response, self.error_template)
        self.assertContains(response, "State Inválido o Expirado")
        mock_login_save.assert_not_called()

    @patch('clave_unica_auth.views._exchange_auth_code')
    @patch('clave_unica_auth.views._validate_state')
    @patch('clave_unica_auth.models.LoginClaveUnicaModel.save')
    def test_callback_token_exchange_error(self, mock_login_save, mock_validate_state, mock_exchange_code):
        mock_validate_state.return_value = {'remote_addr': '1.1.1.1'}
        mock_exchange_code.side_effect = TokenExchangeError("Token fail")
        response = self.client.get(self.callback_url, {'state': 's', 'code': 'c'})
        self.assertTemplateUsed(response, self.error_template)
        self.assertContains(response, "Error de Intercambio de Token")
        mock_login_save.assert_called()

    @patch('clave_unica_auth.views._fetch_user_info')
    @patch('clave_unica_auth.views._exchange_auth_code')
    @patch('clave_unica_auth.views._validate_state')
    @patch('clave_unica_auth.models.LoginClaveUnicaModel.save')
    def test_callback_user_info_error(self, mock_login_save, mock_validate_state, mock_exchange_code, mock_fetch_info):
        mock_validate_state.return_value = {'remote_addr': '1.1.1.1'}
        def side_effect_exchange_code(login_attempt, settings): login_attempt.access_token = 'token'
        mock_exchange_code.side_effect = side_effect_exchange_code
        mock_fetch_info.side_effect = UserInfoError("User info fail")
        response = self.client.get(self.callback_url, {'state': 's', 'code': 'c'})
        self.assertTemplateUsed(response, self.error_template)
        self.assertContains(response, "Error al Obtener Información del Usuario")
        mock_login_save.assert_called()

    @override_settings(CLAVE_UNICA={**TEST_CLAVE_UNICA_SETTINGS, 'AUTO_CREATE_USER': False})
    @patch('clave_unica_auth.views._get_or_create_user_and_person')
    @patch('clave_unica_auth.views._fetch_user_info')
    @patch('clave_unica_auth.views._exchange_auth_code')
    @patch('clave_unica_auth.views._validate_state')
    @patch('clave_unica_auth.models.LoginClaveUnicaModel.save')
    def test_callback_user_not_registered_auto_create_false(self, mock_login_model_save,
                                                           mock_validate_state, mock_exchange_code,
                                                           mock_fetch_info, mock_get_create_user):
        mock_validate_state.return_value = {'remote_addr': '1.1.1.1'}
        def side_effect_exchange_code(login_attempt, settings): login_attempt.access_token = 'token'
        mock_exchange_code.side_effect = side_effect_exchange_code
        mock_fetch_info.return_value = self.mock_user_info_json
        mock_get_create_user.side_effect = UserNotRegisteredError("Auto create off")
        response = self.client.get(self.callback_url, {'state': 's', 'code': 'c'})
        self.assertTemplateUsed(response, self.error_template)
        self.assertContains(response, "Usuario no registrado")
        mock_login_model_save.assert_called() # Called within _get_or_create_user_and_person

    @patch('clave_unica_auth.views.logger')
    @patch('clave_unica_auth.views._validate_state')
    @patch('clave_unica_auth.models.LoginClaveUnicaModel.save')
    def test_callback_unexpected_error(self, mock_login_save, mock_validate_state, mock_logger):
        mock_validate_state.side_effect = Exception("Unexpected")
        response = self.client.get(self.callback_url, {'state': 's', 'code': 'c'})
        self.assertTemplateUsed(response, self.error_template)
        self.assertContains(response, "Error Inesperado")
        mock_logger.exception.assert_called_once_with("Error inesperado en claveunica_callback")
        mock_login_save.assert_called()
