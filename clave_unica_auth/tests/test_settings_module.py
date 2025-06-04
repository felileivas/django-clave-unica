import importlib
import pytest
from django.conf import settings as django_settings
import django


if not django_settings.configured:
    django_settings.configure()
    django.setup()


def reload_settings():
    return importlib.reload(importlib.import_module('clave_unica_auth.settings'))


def test_default_settings(tmp_path):
    django_settings.CLAVE_UNICA = {
        'CLIENT_ID': 'cid',
        'CLIENT_SECRET': 'secret',
        'REDIRECT_URI': 'http://test/'
    }
    mod = reload_settings()
    assert mod.get('CLIENT_ID') == 'cid'
    assert mod.get('URL_LOGIN').startswith('https://accounts.claveunica.gob.cl')


def test_missing_required():
    django_settings.CLAVE_UNICA = {}
    with pytest.raises(Exception):
        reload_settings()
