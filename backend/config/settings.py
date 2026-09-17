import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / '.env', encoding='utf-8-sig')
DEBUG = os.getenv('DEBUG', '0') == '1'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG or 'test' in __import__('sys').argv:
        SECRET_KEY = 'local-development-only-do-not-deploy'
    else:
        raise RuntimeError('Set DJANGO_SECRET_KEY before starting production')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.staticfiles', 'rest_framework', 'study']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': dj_database_url.config(default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'), conn_max_age=60)}
if DATABASES['default']['ENGINE'].endswith('sqlite3'):
    DATABASES['default']['OPTIONS'] = {'timeout': 30, 'transaction_mode': 'IMMEDIATE'}
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
REST_FRAMEWORK = {'EXCEPTION_HANDLER':'study.exceptions.api_exception_handler','DEFAULT_AUTHENTICATION_CLASSES':['rest_framework.authentication.SessionAuthentication'], 'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'], 'DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.UserRateThrottle','rest_framework.throttling.AnonRateThrottle'], 'DEFAULT_THROTTLE_RATES':{'user':'120/min','anon':'30/min'}}
USE_TZ = True
TIME_ZONE = 'UTC'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_URL = '/assets/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR.parent / 'frontend/dist/assets'] if (BASE_DIR.parent / 'frontend/dist/assets').exists() else []
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', '0' if DEBUG else '1') == '1'
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
DATA_UPLOAD_MAX_MEMORY_SIZE = 22 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini' if os.getenv('GEMINI_API_KEY') else 'openai')
AI_MODEL = os.getenv('AI_MODEL', 'gemini-3.6-flash' if AI_PROVIDER == 'gemini' else 'gpt-4.1-mini')
AI_INPUT_PRICE = float(os.getenv('AI_INPUT_PRICE_PER_MILLION', '0.40'))
AI_OUTPUT_PRICE = float(os.getenv('AI_OUTPUT_PRICE_PER_MILLION', '1.60'))
