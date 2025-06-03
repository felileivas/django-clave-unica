import os
from setuptools import find_packages, setup

# Leer el contenido del archivo README.md
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as readme:
    README = readme.read()

# Cambiar al directorio del archivo
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# Configuración del paquete
setup(
    name='django-clave-unica',
    version='2.0.0',
    packages=find_packages(),
    include_package_data=True,
    license='GNU General Public License v3 (GPLv3)',
    description='Aplicación Django para integración con autenticación Clave Única',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://ticraft.cl',
    author='Ticraft.cl',
    author_email='felipe@ticraft.cl',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 5.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    python_requires='>=3.12.7',
    install_requires=[
        'django>=5.1.1',
        'requests==2.32.3',
        'urllib3==2.2.3'
    ],
    project_urls={
        'Documentation': 'https://github.com/felileivas/django-clave-unica',
        'Source': 'https://github.com/felileivas/django-clave-unica',
        'Tracker': 'https://github.com/felileivas/django-clave-unica/issues',
    },
)
