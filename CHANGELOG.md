
# Changelog

Todos los cambios importantes realizados en este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/) y el versionado sigue [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.0.0] - [12/06/25]
### Added
- Migración del proyecto a **Python >= 3.11** y **Django >= 5.0**.
- Incorporación de la licencia **GNU General Public License v3 (GPLv3)** para nuevas contribuciones.
- Documentación actualizada en el archivo `README.md` con instrucciones de instalación, configuración y contribución.
- Implementación de configuraciones avanzadas en `settings.py` para mayor personalización del sistema Clave Única.
- Soporte para **Django 2.2** a **5.1** con proyecto de ejemplo actualizado y archivo `requirements.txt` dedicado.
- Consolidación de migraciones y eliminación de migraciones antiguas.
- Archivo `MANIFEST.in` corregido para una distribución adecuada.
- Se agregaron saltos de línea finales a los archivos que no los tenían.

### Removed
- Referencias al repositorio original en el código y la documentación.
- Archivos `__pycache__` y código muerto.

## [1.0.1] - [14/07/19]
### Added
- Se cambia la configuracion Clave Única a tipo diccionario en settings.py.

## [1.0.0] - [07/07/19]
### Added
- Permite la autenticación de los usuarios via Clave Única.
---