import collections
import sys

# Fix for collections types removed in Python 3.10+ and 3.12
if sys.version_info >= (3, 10):
    # Collections types moved to collections.abc
    if not hasattr(collections, 'Iterator'):
        collections.Iterator = collections.abc.Iterator
    if not hasattr(collections, 'Mapping'):
        collections.Mapping = collections.abc.Mapping
    if not hasattr(collections, 'MutableMapping'):
        collections.MutableMapping = collections.abc.MutableMapping
    if not hasattr(collections, 'Iterable'):
        collections.Iterable = collections.abc.Iterable
    if not hasattr(collections, 'Container'):
        collections.Container = collections.abc.Container
    if not hasattr(collections, 'Sequence'):
        collections.Sequence = collections.abc.Sequence
    if not hasattr(collections, 'MutableSequence'):
        collections.MutableSequence = collections.abc.MutableSequence
    if not hasattr(collections, 'Set'):
        collections.Set = collections.abc.Set
    if not hasattr(collections, 'MutableSet'):
        collections.MutableSet = collections.abc.MutableSet

# Fix for gettext codeset parameter in Python 3.12
if sys.version_info >= (3, 12):
    import gettext
    _original_translation = gettext.translation
    
    def _patched_translation(*args, **kwargs):
        if 'codeset' in kwargs:
            del kwargs['codeset']
        return _original_translation(*args, **kwargs)
    
    gettext.translation = _patched_translation

import os

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent 


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ur9rs%j+b8ry!#ra_p799%(+vns-r$xf70350v$!&(t@bhyuc_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

SITE_ID = 1

LOGIN_URL = '/accounts/login/'                    # Path to login page
LOGIN_REDIRECT_URL = '/'                          # Where to go after login (home)
LOGOUT_REDIRECT_URL = '/'          # Where to go after logout


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',      
    'allauth',                   
    'allauth.account',
    'allauth.socialaccount',           
    'corsheaders', 
 #   'debug_toolbar', 
     'model_utils',
     'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks', 
    'django_extensions',
 #   'forms_builder.forms',

    
    'geography.apps.GeographyConfig',
    'accounts.apps.AccountsConfig', # CustomUser model is here
    'membership.apps.MembershipConfig',
    'utils.apps.UtilsConfig',
    'pdf_processor.apps.PdfProcessorConfig',  # Manages PDF generation and processing functionalities
    'competitions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
]

ROOT_URLCONF = 'safa_global.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INTERNAL_IPS = [
    '127.0.0.1',
]

WSGI_APPLICATION = 'safa_global.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development, use console backend
DEFAULT_FROM_EMAIL = 'shaunqjohannes@gmail.com'  # Change to your default email address
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Or 'email', as you prefer
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'           # Or 'mandatory'
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/m",  # 5 failed logins per minute
    # You can adjust the rate as needed, e.g. "10/h" for 10 per hour
}

# Optional:
# ACCOUNT_SIGNUP_REDIRECT_URL = '/your-signup-complete/'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
