import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD: En producción (Render), estas variables se leen desde el entorno
SECRET_KEY = os.environ.get('SECRET_KEY', 'vicky-django-clave-secreta-2026-xyz')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # Cambiado a False por defecto para producción

ALLOWED_HOSTS = ['*']  # En Render puedes cambiar '*' por tu dominio específico .onrender.com

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'correos.apps.CorreosConfig',  # Tu aplicación de correos
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Manejo eficiente de CSS/JS en Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# APLICACIÓN WSGI
WSGI_APPLICATION = 'config.wsgi.application'

# CONEXIÓN A BASE DE DATOS (Render PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://victoria:C5ukfhCktDhuThKp9KFQdG3n2SbAu6Nl@dpg-d8gqkn6k1jcs73dajjg0-a.oregon-postgres.render.com/api_db_hzbz'
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# CONFIGURACIÓN DE IDIOMA Y HORARIO
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# ARCHIVOS ESTÁTICOS (WhiteNoise)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# CONFIGURACIÓN DE EMAIL SEGURA PARA GMAIL API / DIRECT SMTP EN RENDER
# ==============================================================================
# Usamos el backend de memoria local de Django para desactivar sus puertos nativos.
# El envío real se gestiona directamente encriptado desde el archivo admin.py.
# Asegúrate de que las últimas líneas queden EXACTAMENTE así:

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Línea 90 y 91 corregidas:
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'vicky190486@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'invhbmxvfdtsfyqv')