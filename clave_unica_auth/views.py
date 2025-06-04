from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth import login

from .lib.utils import oauth2_claveunica
from .models import Login as LoginClaveUnica, Person as PersonClaveUnica
from clave_unica_auth import settings as claveunica_settings

def claveunica_login(request):
    """Redirect a Clave Unica"""
    state = oauth2_claveunica.generate_state()
    cache.set(
        state,
        {"remote_addr": request.META.get("REMOTE_ADDR")},
        claveunica_settings.get("STATE_TIMEOUT"),
    )
    url = oauth2_claveunica.get_url_login_claveunica(
        claveunica_settings.get("URL_LOGIN"),
        claveunica_settings.get("CLIENT_ID"),
        claveunica_settings.get("REDIRECT_URI"),
        state,
    )
    return redirect(url)

def claveunica_callback(request):
    """Intercambio authorization_code a access_token y obtener info de usuario"""
    state = request.GET.get("state")
    code = request.GET.get("code")
    if not state or not code:
        return claveunica_error(
            request,
            {
                "error": "Respuesta incompleta",
                "description": "No se recibieron los parametros requeridos.",
            },
        )

    cache_data = cache.get(state)
    if cache_data is None:
        context = {
            "error": "State expirado",
            "description": "El parametro state ha expirado. Por favor, vuelva a iniciar sesion.",
        }
        return claveunica_error(request, context)
    cache.delete(state)

    login_record = LoginClaveUnica(
        state=state,
        authorization_code=code,
        remote_addr=cache_data.get("remote_addr"),
    )

    try:
        access_token_json = oauth2_claveunica.request_authorization_code(
            claveunica_settings.get("TOKEN_URI"),
            claveunica_settings.get("CLIENT_ID"),
            claveunica_settings.get("CLIENT_SECRET"),
            claveunica_settings.get("REDIRECT_URI"),
            login_record.authorization_code,
            login_record.state,
        )
        login_record.access_token = access_token_json.get("access_token")
        info_user_json = oauth2_claveunica.request_info_user(
            claveunica_settings.get("USERINFO_URI"),
            login_record.access_token,
        )
    except Exception as e:
        login_record.save()
        return claveunica_error(
            request,
            {
                "error": str(e) or "Error en Clave Unica",
                "description": str(e),
            },
        )

    try:
        username = f"{info_user_json['RolUnico']['numero']}-{info_user_json['RolUnico']['DV']}"
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        if claveunica_settings.get("AUTO_CREATE_USER"):
            person = PersonClaveUnica()
            person.parse_json(info_user_json)
            user = person.parse_json_to_user(info_user_json)
            user.save()
            person.user = user
            person.save()
        else:
            login_record.save()
            return claveunica_error(
                request,
                {
                    "error": "Usuario no registrado",
                    "description": "El usuario no se encuentra actualmente registrado.",
                },
            )

    if user is not None:
        login(request, user)
        login_record.user = user
        login_record.completed = True
        login_record.save()
        return redirect(claveunica_settings.get("PATH_SUCCESS_LOGIN"))

    login_record.save()
    return claveunica_error(
        request,
        {
            "error": "Error en autenticacion",
            "description": "No se ha logrado autenticar el usuario.",
        },
    )

def claveunica_error(request, context=None):
    """Error vista clave unica"""
    if context is None:
        context = {
            'error': 'Error autenticación',
            'description': 'Error en autenticación del usuario.'
        }
    if not claveunica_settings.get('REMEMBER_LOGIN'):
        context['url_logout'] = claveunica_settings.get('URL_LOGOUT')
    return render(request, claveunica_settings.get('HTML_ERROR'), context)
