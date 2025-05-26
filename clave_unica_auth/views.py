"""
Vistas para el proceso de autenticación con ClaveÚnica.

Este módulo contiene las vistas que manejan el flujo de OAuth2 con ClaveÚnica:
- `claveunica_login`: Redirige al usuario a la página de login de ClaveÚnica.
- `claveunica_callback`: Maneja la respuesta de ClaveÚnica después del login,
  intercambia el código de autorización por un token de acceso, obtiene la
  información del usuario, y autentica o crea al usuario en el sistema local.
- `claveunica_error`: Muestra una página de error.
"""
"""
Vistas para el proceso de autenticación con ClaveÚnica.

Este módulo contiene las vistas que manejan el flujo de OAuth2 con ClaveÚnica:
- `claveunica_login`: Redirige al usuario a la página de login de ClaveÚnica.
- `claveunica_callback`: Maneja la respuesta de ClaveÚnica después del login,
  intercambia el código de autorización por un token de acceso, obtiene la
  información del usuario, y autentica o crea al usuario en el sistema local.
- `claveunica_error`: Muestra una página de error.
"""
import logging

from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth import login

from .lib.utils import oauth2_claveunica
from .models import Login as LoginClaveUnica, Person as PersonClaveUnica
from clave_unica_auth.settings import app_settings
from .exceptions import (
    InvalidStateError, TokenExchangeError, UserInfoError, UserNotRegisteredError,
    ClaveUnicaAPIError # Import ClaveUnicaAPIError
)

logger = logging.getLogger(__name__)

def claveunica_login(request):
    """Redirect a Clave Unica"""
    state = oauth2_claveunica.generate_state()
    cache.set(state, { 'remote_addr': request.META.get('REMOTE_ADDR') }, app_settings.STATE_TIMEOUT)
    return redirect(oauth2_claveunica.get_url_login_claveunica(app_settings.URL_LOGIN, app_settings.CLIENT_ID, app_settings.REDIRECT_URI, state))

def _validate_state(request_state, cache_backend):
    """Validates state and retrieves data from cache."""
    if not request_state:
        raise InvalidStateError("El parámetro 'state' no se encontró en la solicitud.")
    cache_data = cache_backend.get(request_state)
    if cache_data is None:
        raise InvalidStateError("State expirado o inválido. Por favor, vuelva a iniciar sesión.")
    cache_backend.delete(request_state)
    return cache_data

def _exchange_auth_code(login_instance, current_app_settings):
    """Exchanges authorization code for access token."""
    try:
        access_token_json = oauth2_claveunica.request_authorization_code(
            current_app_settings.TOKEN_URI,
            current_app_settings.CLIENT_ID,
            current_app_settings.CLIENT_SECRET,
            current_app_settings.REDIRECT_URI,
            login_instance.authorization_code,
            login_instance.state
        )
        login_instance.access_token = access_token_json.get('access_token')
        if not login_instance.access_token:
            # This case should ideally be covered by ClaveUnicaAPIError if the API returns an unexpected response
            raise TokenExchangeError("No se recibió access_token en la respuesta de ClaveÚnica.")
        return access_token_json
    except ClaveUnicaAPIError as e:
        # Re-raise ClaveUnicaAPIError as TokenExchangeError for specific handling in callback
        raise TokenExchangeError(f"Error de API ClaveÚnica durante el intercambio de token: {e}")
    except Exception as e: # Catch any other unexpected exceptions
        logger.error(f"Error inesperado durante el intercambio de código de autorización: {e}", exc_info=True)
        raise TokenExchangeError(f"Error inesperado al intercambiar código de autorización: {e}")

def _fetch_user_info(access_token, current_app_settings):
    """Fetches user information from ClaveUnica."""
    try:
        info_user_json = oauth2_claveunica.request_info_user(
            current_app_settings.USERINFO_URI,
            access_token
        )
        return info_user_json
    except ClaveUnicaAPIError as e:
        # Re-raise ClaveUnicaAPIError as UserInfoError for specific handling in callback
        raise UserInfoError(f"Error de API ClaveÚnica al obtener información del usuario: {e}")
    except Exception as e: # Catch any other unexpected exceptions
        logger.error(f"Error inesperado al obtener información del usuario: {e}", exc_info=True)
        raise UserInfoError(f"Error inesperado al obtener información del usuario: {e}")

def _get_or_create_user_and_person(info_user_json, current_app_settings, login_instance):
    """Gets or creates User and PersonClaveUnica instances."""
    # Username generation logic is now inside create_user_from_claveunica_data,
    # but we might need it for the lookup.
    # We should aim to use the same source of truth for username generation.
    # For now, let's assume RolUnico and its parts are present for lookup,
    # create_user_from_claveunica_data will validate them again.
    rol_unico_data = info_user_json.get('RolUnico', {})
    run = rol_unico_data.get('numero')
    dv = rol_unico_data.get('DV')

    if not run or not dv:
        # This case should ideally be caught by _fetch_user_info if the response is malformed.
        # Or, if RolUnico is optional, this indicates an issue that needs specific handling.
        # For now, mirroring the previous behavior, this will lead to an error later if not handled.
        # However, create_user_from_claveunica_data will raise a ValueError if this happens.
        # We can pre-emptively raise an error or let the class method handle it.
        # Let's rely on the class method for now.
        pass # Username will be None, User.objects.get will fail.

    username = f"{run}-{dv}" if run and dv else None
    
    try:
        user = User.objects.get(username=username)
        # If user exists, ensure PersonClaveUnica record is also up-to-date or exists
        # This part was missing in the original logic but is good practice.
        # For now, just returning the user as per original logic if found.
        return user
    except User.DoesNotExist:
        if current_app_settings.AUTO_CREATE_USER:
            # Create the User object using the new class method
            try:
                user = PersonClaveUnica.create_user_from_claveunica_data(info_user_json)
                user.save()
            except ValueError as e:
                # Handle cases where data for user creation is invalid (e.g. missing RUN/DV)
                # Log this error, save login_instance, and re-raise or return specific error context
                logger.error(f"Error creating user from ClaveUnica data: {e}")
                login_instance.save()
                # Propagate as a generic UserInfoError or a more specific one if desired
                raise UserInfoError(f"Datos insuficientes o inválidos de ClaveUnica para crear el usuario: {e}")

            # Create and save the PersonClaveUnica object
            person_clave_unica = PersonClaveUnica()
            person_clave_unica.parse_json(info_user_json) # Populates run_type, run_num, run_dv
            person_clave_unica.user = user
            person_clave_unica.save()
            return user
        else:
            # login_instance should be saved before raising UserNotRegisteredError
            login_instance.save() 
            raise UserNotRegisteredError("Usuario no registrado y la creación automática está deshabilitada.")
    except ValueError as e: # Catch ValueError from create_user_from_claveunica_data if username was None
        logger.error(f"Error determining username for lookup or during user creation: {e}")
        login_instance.save()
        raise UserInfoError(f"Datos inválidos de ClaveUnica para determinar el nombre de usuario: {e}")


def claveunica_callback(request):
    """Intercambio authorization_code a access_token y obtener info de usuario"""
    state_param = request.GET.get('state')
    code_param = request.GET.get('code')

    login_attempt = LoginClaveUnica()
    login_attempt.state = state_param
    login_attempt.authorization_code = code_param
    
    try:
        cache_data = _validate_state(state_param, cache)
        login_attempt.remote_addr = cache_data.get('remote_addr')

        _exchange_auth_code(login_attempt, app_settings) # Updates login_attempt.access_token
        
        user_info_json = _fetch_user_info(login_attempt.access_token, app_settings)
        
        user = _get_or_create_user_and_person(user_info_json, app_settings, login_attempt)

        # If _get_or_create_user_and_person did not raise UserNotRegisteredError and user is None (should not happen with current logic)
        # this is a fallback, but primarily UserNotRegisteredError should be caught.
        if not user:
             login_attempt.save()
             context = {'error': 'Error en autenticación', 'description': 'No se pudo obtener o crear el usuario.'}
             return claveunica_error(request, context)

        login(request, user)
        login_attempt.user = user
        login_attempt.completed = True
        login_attempt.save()
        return redirect(app_settings.PATH_SUCCESS_LOGIN)

    except InvalidStateError as e:
        # No need to save login_attempt as no interaction with ClaveUnica happened yet.
        context = {'error': 'State Inválido o Expirado', 'description': str(e)}
        return claveunica_error(request, context)
    except TokenExchangeError as e:
        login_attempt.save() # Save the attempt with the auth code
        context = {'error': 'Error de Intercambio de Token', 'description': str(e)}
        return claveunica_error(request, context)
    except UserInfoError as e:
        login_attempt.save() # Save the attempt with the access token
        context = {'error': 'Error al Obtener Información del Usuario', 'description': str(e)}
        return claveunica_error(request, context)
    except UserNotRegisteredError as e:
        # login_attempt is already saved in _get_or_create_user_and_person before raising this
        context = {'error': 'Usuario no registrado', 'description': str(e)}
        return claveunica_error(request, context)
    except Exception as e:
        login_attempt.save()
        logger.exception("Error inesperado en claveunica_callback") # Log the full traceback
        context = {'error': 'Error Inesperado', 'description': 'Ha ocurrido un error inesperado durante la autenticación. Contacte al administrador.'}
        return claveunica_error(request, context)

def claveunica_error(request, context={'error': 'Error autenticación', 'description': 'Error en autenticación del usuario.'}):
    """Error vista clave unica"""
    if not app_settings.REMEMBER_LOGIN:
        context['url_logout'] = app_settings.URL_LOGOUT
    return render(request, app_settings.HTML_ERROR, context)