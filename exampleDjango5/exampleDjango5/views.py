from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings

def index(request):
    """
    Vista para renderizar la página de inicio.
    """
    return render(request, 'index.html')

@login_required
def home(request):
    """
    Vista para renderizar la página principal después de autenticarse.
    Incluye un enlace para cerrar sesión si `REMEMBER_LOGIN` no está habilitado.
    """
    context = {}
    remember_login = getattr(settings, 'CLAVE_UNICA', {}).get('REMEMBER_LOGIN', True)
    if not remember_login:
        url_logout = getattr(settings, 'CLAVE_UNICA', {}).get('URL_LOGOUT', '/logout/')
        context = {'url_logout': url_logout}
    return render(request, 'home.html', context)

def logout(request):
    """
    Vista para cerrar la sesión del usuario.
    Redirige a la página de inicio después de cerrar la sesión.
    """
    auth_logout(request)
    return redirect(reverse('index'))