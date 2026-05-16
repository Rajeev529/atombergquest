
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

CSRF_TRUSTED_ORIGINS = [
    "https://atombergquest-production.up.railway.app",
]

ALLOWED_HOSTS = [
    "atombergquest-production.up.railway.app",
    "localhost",
    "127.0.0.1",
]
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.theme_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# # Database
# import dj_database_url
# if(os.getenv('DEBUG')=='False'):
#     DATABASES = {
#         'default': dj_database_url.config(
#             default=os.getenv('DBURL'),
#             conn_max_age=600,  # Persistent connections for performance
#         )
#     }
# else:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql',
#             'NAME': os.getenv('DB_NAME'),
#             'USER': os.getenv('DB_USER'),
#             'PASSWORD': os.getenv('DB_PASSWORD'),
#             'HOST': os.getenv('DB_HOST'),
#             'PORT': os.getenv('DB_PORT'),
#             'OPTIONS': {
#                 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#             },
#         }
#     }


import dj_database_url

DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DBURL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'app.User'

# Login URL
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Email settings (console backend for demo)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# Demo Mode - bypass date restrictions
DEMO_MODE = os.getenv('DEMO_MODE', 'False') == 'True'

# Thrust Areas
THRUST_AREAS = [
    ('SALES', 'Sales & Revenue'),
    ('CUSTOMER', 'Customer Success'),
    ('PRODUCT', 'Product Development'),
    ('OPERATIONS', 'Operations Excellence'),
    ('PEOPLE', 'People & Culture'),
    ('FINANCE', 'Financial Management'),
    ('COMPLIANCE', 'Compliance & Risk'),
    ('INNOVATION', 'Innovation & Growth'),
]

# UoM Types
UOM_TYPES = [
    ('NUMERIC', 'Numeric (Higher is better)'),
    ('PERCENTAGE', 'Percentage (Higher is better)'),
    ('TIMELINE', 'Timeline (Date-based)'),
    ('ZERO', 'Zero-based (Zero = Success)'),
]

# UoM Direction
UOM_DIRECTION = [
    ('MIN', 'Higher is better (Achievement ÷ Target)'),
    ('MAX', 'Lower is better (Target ÷ Achievement)'),
]

# Goal Status
GOAL_STATUS = [
    ('NOT_STARTED', 'Not Started'),
    ('ON_TRACK', 'On Track'),
    ('COMPLETED', 'Completed'),
]

# Quarter Types
QUARTER_TYPES = [
    ('Q1', 'Q1 (July)'),
    ('Q2', 'Q2 (October)'),
    ('Q3', 'Q3 (January)'),
    ('Q4', 'Q4 (March/April)'),
    ('GOAL_SETTING', 'Goal Setting (May)'),
]

# Themes
AVAILABLE_THEMES = {
    'ocean': {'name': 'Ocean Breeze', 'free': True, 'icon': '🌊'},
    'sunset': {'name': 'Sunset Glow', 'free': True, 'icon': '🌅'},
    'forest': {'name': 'Forest Magic', 'free': False, 'icon': '🌲', 'required_performance': 70},
    'midnight': {'name': 'Midnight Galaxy', 'free': False, 'icon': '🌙', 'required_performance': 85},
}
