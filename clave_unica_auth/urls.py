"""
URL patterns for the clave_unica_auth application.

Defines paths for the login initiation and callback handling views
for the ClaveÚnica authentication process.
"""
from django.urls import path

from clave_unica_auth.settings import app_settings
from .views import claveunica_login, claveunica_callback

urlpatterns = [
    path(app_settings.PATH_LOGIN, claveunica_login, name='clave_unica_auth-login'),
    path(app_settings.PATH_REDIRECT, claveunica_callback, name='clave_unica_auth-callback'),
]
