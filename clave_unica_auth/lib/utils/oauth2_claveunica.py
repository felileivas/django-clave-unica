"""
Utilidades para la interacción con el protocolo OAuth2 de ClaveÚnica.

Este módulo proporciona funciones para construir URLs, preparar parámetros
y realizar solicitudes a los endpoints de ClaveÚnica para la autenticación
y obtención de información del usuario.
"""
from urllib.parse import urlencode
import uuid
import requests

from clave_unica_auth.settings import app_settings
from clave_unica_auth.exceptions import ClaveUnicaAPIError


def generate_state():
    """Generar un UUIDv4 aleatorio para el parámetro 'state'."""
    return str(uuid.uuid4())


def encode_dict_to_uri(params):
    """Codificar un diccionario a formato URI."""
    return urlencode(params)


def join_url_with_params(url, params):
    """Construir una URL completa uniéndola con sus parámetros."""
    return f'{url}?{params}'


def get_url_params_authorization_code(client_id, redirect_uri, state, scope):
    """Obtener los parámetros codificados para la solicitud del código de autorización."""
    return encode_dict_to_uri({
        'client_id': client_id,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state,
    })


def get_params_access_token(client_id, client_secret, redirect_uri, code, state):
    """Obtener los parámetros para la solicitud del token de acceso."""
    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'code': code,
        'state': state,
    }

def get_headers_authorization_code():
    """Obtener los encabezados para la solicitud del código de autorización."""
    return {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'User-Agent': app_settings.USER_AGENT
    }


def get_headers_bearer_token(access_token):
    """Obtener los encabezados para la autenticación Bearer OAuth2."""
    return {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'User-Agent': app_settings.USER_AGENT
    }


def get_url_login_claveunica(url, client_id, redirect_uri, state=uuid.uuid4()):
    """Obtener la URL completa para redirigir al login de ClaveÚnica."""
    scope = app_settings.OAUTH_SCOPE
    params = get_url_params_authorization_code(client_id, redirect_uri, state, scope)
    return join_url_with_params(url, params)


def request_authorization_code(url, client_id, client_secret, redirect_uri, code, state):
    """Realizar la solicitud POST para intercambiar el código de autorización por un token de acceso."""
    try:
        resp = requests.post(
            url,
            data=get_params_access_token(client_id, client_secret, redirect_uri, code, state),
            headers=get_headers_authorization_code()
        )
        if resp.status_code != 200:
            error_details = ""
            try:
                data = resp.json()
                error_details = data.get('error_description', data.get('error', resp.text))
            except requests.exceptions.JSONDecodeError:
                error_details = resp.text
            raise ClaveUnicaAPIError(
                f"Clave Unica API error ({resp.status_code}) durante el intercambio de token: {error_details}"
            )
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise ClaveUnicaAPIError(f"Error de red durante el intercambio de token: {e}")


def request_info_user(url, access_token):
    """Realizar la solicitud POST para obtener la información del usuario desde ClaveÚnica."""
    try:
        resp = requests.post(url, headers=get_headers_bearer_token(access_token))
        if resp.status_code != 200:
            error_details = ""
            try:
                data = resp.json()
                error_details = data.get('error_description', data.get('error', resp.text))
            except requests.exceptions.JSONDecodeError:
                error_details = resp.text
            raise ClaveUnicaAPIError(
                f"Clave Unica API error ({resp.status_code}) durante la obtención de información del usuario: {error_details}"
            )
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise ClaveUnicaAPIError(f"Error de red durante la obtención de información del usuario: {e}")
