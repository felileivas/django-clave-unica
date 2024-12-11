# Django Clave Única

Aplicación Django para la autenticación de ciudadanos chilenos mediante **Clave Única**.  
Este proyecto está diseñado para integrarse fácilmente con el sistema de identidad digital de Clave Única, garantizando una autenticación segura y centralizada.

Este proyecto es una versión derivada de https://github.com/GatoSnake/django-clave-unica, que está licenciado bajo la licencia ISC. Las modificaciones realizadas por Ticraft.cl están licenciadas bajo GNU GPL v3.

Este repositorio es una versión actualizada y mantenida activamente por [Ticraft.cl](https://ticraft.cl), adaptada para soportar:

- **Python** >= 3.12.7
- **Django** >= 5.1.1

## 🚀 Funcionalidades
- Autenticación basada en OAuth2 con Clave Única.
- Creación automática de usuarios a partir de los datos proporcionados por Clave Única.
- Gestión de sesiones segura y configurable.
- Configuraciones flexibles para personalizar URLs, tiempos de expiración y comportamientos.

## 🛠 Instalación

Sigue estos pasos para instalar y configurar el proyecto:

1. **Instala el paquete**:
   ```bash
   pip install django-clave-unica
   ```

2. **Configura tu aplicación**:
   En el archivo `settings.py`, añade:
   ```python
   INSTALLED_APPS = [
       ...
       'clave_unica_auth',
   ]

   CLAVE_UNICA = {
       'CLIENT_ID': 'tu_client_id',
       'CLIENT_SECRET': 'tu_client_secret',
       'REDIRECT_URI': 'tu_redirect_uri',
   }
   ```

3. **Incluye las rutas**:
   En el archivo `urls.py`, añade:
   ```python
   from django.urls import include, path

   urlpatterns = [
       ...
       path('claveunica/', include('clave_unica_auth.urls')),
   ]
   ```

4. **Aplica migraciones**:
   ```bash
   python manage.py migrate
   ```

5. **Inicia el servidor de desarrollo**:
   ```bash
   python manage.py runserver
   ```

Accede a [http://127.0.0.1:8000/claveunica/login](http://127.0.0.1:8000/claveunica/login) para probar el inicio de sesión.

---

## 🧑‍💻 Configuraciones Avanzadas

### Clave Única
Puedes personalizar el comportamiento del sistema mediante las siguientes configuraciones en `settings.py`:

| Configuración                 | Tipo    | Predeterminado                                            | Descripción                                   |
|-------------------------------|---------|----------------------------------------------------------|-----------------------------------------------|
| `CLIENT_ID`                   | string  | -                                                        | ID del cliente proporcionado por Clave Única.|
| `CLIENT_SECRET`               | string  | -                                                        | Clave secreta del cliente.                   |
| `REDIRECT_URI`                | string  | -                                                        | URL de redirección registrada en Clave Única.|
| `URL_LOGIN`                   | string  | `https://accounts.claveunica.gob.cl/openid/authorize`    | URL para login en Clave Única.               |
| `URL_LOGOUT`                  | string  | `https://api.claveunica.gob.cl/api/v1/accounts/app/logout` | URL para logout en Clave Única.              |
| `REMEMBER_LOGIN`              | boolean | `False`                                                  | Permite recordar la sesión del usuario.      |
| `TOKEN_URI`                   | string  | `https://accounts.claveunica.gob.cl/openid/token`        | URL para intercambiar `authorization_code` por `access_token`. |
| `USERINFO_URI`                | string  | `https://accounts.claveunica.gob.cl/openid/userinfo`     | URL para obtener información del usuario.    |
| `STATE_TIMEOUT`               | int     | `1800` (30 minutos)                                      | Tiempo de expiración del parámetro `state`.  |
| `AUTO_CREATE_USER`            | boolean | `True`                                                   | Crea automáticamente al usuario si no existe.|
| `PATH_LOGIN`                  | string  | `login/`                                                 | Path interno hacia la vista de login.        |
| `PATH_REDIRECT`               | string  | `callback/`                                              | Path interno para redirección desde Clave Única. |
| `PATH_SUCCESS_LOGIN`          | string  | `/home/`                                                 | Path interno tras inicio de sesión exitoso.  |
| `HTML_ERROR`                  | string  | `clave_unica_auth/error.html`                            | Path al archivo HTML para errores.           |

Consulta la documentación oficial en [https://digital.gob.cl/](https://digital.gob.cl/transformacion-digital/estandares-y-guias/guia-tecnica-para-integracion-de-claveunica/) para obtener tus credenciales.

---

## 📖 Documentación

- **Ejemplos de uso**: Ver el directorio `exampleDjango2.2.3/`.
- **Changelog**: Todas las actualizaciones están documentadas en el archivo `CHANGELOG.md`.

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Sigue estos pasos para colaborar:

1. Haz un fork del repositorio.
2. Crea una nueva rama para tu funcionalidad o corrección de errores (`git checkout -b mi-nueva-funcionalidad`).
3. Realiza tus cambios y escribe pruebas para los mismos.
4. Envía un pull request explicando tu contribución.

---

## 🧾 Licencia

Este proyecto está licenciado bajo la **GNU General Public License v3 (GPLv3)**. Consulta el archivo `LICENSE` para más información.

---

