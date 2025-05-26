"""
Application configuration for the clave_unica_auth app.
"""
from django.apps import AppConfig


class ClaveUnicaAuthConfig(AppConfig):
    """
    Configuration class for the 'clave_unica_auth' Django application.
    
    Sets the application name and verbose name for display in the Django admin
    and other parts of the framework.
    """
    name = 'clave_unica_auth'
    verbose_name = 'Clave Única'
