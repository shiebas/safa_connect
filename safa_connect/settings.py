import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent 


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ur9rs%j+b8ry!#ra_p799%(+vns-r$xf70350v$!&(t@bhyuc_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['.ngrok-free.app', 'localhost', '127.0.0.1']

SITE_ID = 1

LOGIN_URL = '/local-accounts/login/'
LOGIN_REDIRECT_URL = '/local-accounts/profile/'  # Redirect to dashboard after login
LOGOUT_REDIRECT_URL = '/'  # Redirect to home after logout (fix the test page issue)


# Application definition

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'django.contrib.humanize', # For human-friendly numbers and dates
    
    # Third party apps
    'rest_framework',  # Added for Django REST Framework
    'rest_framework.authtoken',  # Added for DRF token authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    
    # Local apps - cleaned up
    'geography.apps.GeographyConfig',
    'accounts.apps.AccountsConfig',
    'membership.apps.MembershipConfig',
    'utils.apps.UtilsConfig',
    'pdf_processor.apps.PdfProcessorConfig',
    'membership_cards',
    
    'league_management',  # Competition management system
    # 'tools',  # REMOVED - functionality moved to other apps
    'supporters',
    'events.apps.EventsConfig',  # International events & ticketing
    'merchandise.apps.MerchandiseConfig',  # SAFA merchandise store
    'pwa.apps.PwaConfig',  # Progressive Web App functionality
    'legal.apps.LegalConfig',  # Legal pages (Terms, Privacy, etc.)
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
    'accounts.middleware.AdminFormErrorMiddleware',
    'accounts.middleware.DocumentAccessMiddleware',  # Document tracking and watermarking
]

ROOT_URLCONF = 'safa_connect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # Global templates
        ],
        'APP_DIRS': True,  # Enables app-specific template directories
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

WSGI_APPLICATION = 'safa_connect.wsgi.application'

AUTHENTICATION_BACKENDS = [
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
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS': {'min_length': 8,}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
    {'NAME': 'accounts.validators.ComplexPasswordValidator',}
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
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'

# Email Configuration
# For development, print emails to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'  # or your SMTP server
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'SAFA Registration <noreply@safaconnect.co.za>'

# Site Configuration
#SITE_URL = 'https://registration.safa.net'  # Your production URL


ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email', 'password1']
ACCOUNT_ADAPTER = 'accounts.adapter.CustomAccountAdapter'


# ACCOUNT_RATE_LIMITS = {
#     "login_failed": "5/m",  # 5 failed logins per minute
#     # You can adjust the rate as needed, e.g. "10/h" for 10 per hour
# }

# Optional:
# ACCOUNT_SIGNUP_REDIRECT_URL = '/your-signup-complete/'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Google Wallet Settings
GOOGLE_WALLET_ENABLED = True
GOOGLE_WALLET_ISSUER_ID = '3388000000022222228'  # Replace with actual issuer ID in production
GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL = 'safa-wallet-service@safa-global.iam.gserviceaccount.com'  # Replace with actual service account
GOOGLE_WALLET_KEY_FILE = os.path.join(BASE_DIR, 'credentials', 'google_wallet_key.json')  # Path to service account key file

# Create directory for credentials if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'credentials'), exist_ok=True)

# Base URL for generating absolute URLs (for Google Wallet integration)
BASE_URL = 'https://safaconnect.net'  # Replace with actual domain in production
if DEBUG:
    BASE_URL = 'http://localhost:8000'

GDAL_LIBRARY_PATH = r'C:\Users\User\documents\safa_connect\venv\Lib\site-packages\osgeo\gdal.dll'

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# SAFA Specific Settings
SAFA_DEFAULT_REGISTRATION_FEE = 200.00
SAFA_ENABLE_AUTO_APPROVAL = False
SAFA_REQUIRE_DOCUMENT_VALIDATION = True

# Pagination Settings
PAGINATE_BY = 10

# Security Settings for Production
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG', # Set to DEBUG to see all messages
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO', # Keep Django's own logs at INFO to avoid too much verbosity
            'propagate': False,
        },
        'accounts': { # Logger for your 'accounts' app
            'handlers': ['console'],
            'level': 'DEBUG', # Set to DEBUG for your app's logs
            'propagate': False,
        },
        '': { # Root logger - catches all messages not handled by other loggers
            'handlers': ['console'],
            'level': 'INFO', # Default level for other apps
            'propagate': False,
        },
    }
}