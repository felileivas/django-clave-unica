"""
Handles settings for the clave_unica_auth application.

Provides a mechanism to define default settings, override them with
project-specific settings (defined in `settings.CLAVE_UNICA`), and
access them using an `app_settings` object.
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULTS = {
    'URL_LOGIN': 'https://accounts.claveunica.gob.cl/openid/authorize',
    'URL_LOGOUT': 'https://api.claveunica.gob.cl/api/v1/accounts/app/logout',
    'REMEMBER_LOGIN': False,
    'TOKEN_URI': 'https://accounts.claveunica.gob.cl/openid/token',
    'USERINFO_URI': 'https://accounts.claveunica.gob.cl/openid/userinfo',
    'STATE_TIMEOUT': 60 * 30,  # 30 minutes
    'AUTO_CREATE_USER': True,
    'PATH_LOGIN': 'login/',
    'PATH_REDIRECT': 'callback/',
    'PATH_SUCCESS_LOGIN': '/home/',
    'HTML_ERROR': 'clave_unica_auth/error.html',
    'OAUTH_SCOPE': 'openid run name',
    'USER_AGENT': 'Django ClaveUnica Auth Client 1.0',
    # Required settings (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) will not have defaults here.
}

def get_setting(setting_name):
    # Get the project's CLAVE_UNICA settings dictionary
    project_settings = getattr(settings, 'CLAVE_UNICA', {})
    
    # Check if the setting is in the project settings
    if setting_name in project_settings:
        return project_settings[setting_name]
    
    # If not, and it's a required setting without a default, raise an error
    if setting_name in ['CLIENT_ID', 'CLIENT_SECRET', 'REDIRECT_URI'] and setting_name not in DEFAULTS:
        raise ImproperlyConfigured(f"Required ClaveUnica setting '{setting_name}' is not defined in settings.CLAVE_UNICA.")
        
    # Otherwise, return the default value
    return DEFAULTS.get(setting_name)

# Make settings available for import, e.g. app_settings.CLIENT_ID
class AppSettings:
    def __getattr__(self, name):
        return get_setting(name)

app_settings = AppSettings()
