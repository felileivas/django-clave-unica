from django.conf import settings


DEFAULTS = {
    'URL_LOGIN': 'https://accounts.claveunica.gob.cl/openid/authorize',
    'URL_LOGOUT': 'https://api.claveunica.gob.cl/api/v1/accounts/app/logout',
    'REMEMBER_LOGIN': False,
    'TOKEN_URI': 'https://accounts.claveunica.gob.cl/openid/token',
    'USERINFO_URI': 'https://accounts.claveunica.gob.cl/openid/userinfo',
    'STATE_TIMEOUT': 60 * 30,
    'AUTO_CREATE_USER': True,
    'PATH_LOGIN': 'login/',
    'PATH_REDIRECT': 'callback/',
    'PATH_SUCCESS_LOGIN': '/home/',
    'HTML_ERROR': 'clave_unica_auth/error.html',
}

REQUIRED = {'CLIENT_ID', 'CLIENT_SECRET', 'REDIRECT_URI'}


class ClaveUnicaSettings:
    """Simple wrapper around ``settings.CLAVE_UNICA`` with defaults."""

    def __init__(self):
        user_settings = getattr(settings, 'CLAVE_UNICA', {})
        if not isinstance(user_settings, dict):
            raise Exception('CLAVE_UNICA must be a dict in your Django settings')
        missing = REQUIRED - user_settings.keys()
        if missing:
            names = ', '.join(missing)
            raise Exception(
                "You must set CLAVE_UNICA['{}'] in your settings.".format(names)
            )
        self._settings = {**DEFAULTS, **user_settings}

    def __getattr__(self, name):
        try:
            return self._settings[name]
        except KeyError:
            raise AttributeError(name)


claveunica_settings = ClaveUnicaSettings()


def get(name):
    try:
        return getattr(claveunica_settings, name)
    except AttributeError:
        raise Exception(
            "You must set CLAVE_UNICA['{name_setting}'] in your settings.".format(
                name_setting=name
            )
        )
