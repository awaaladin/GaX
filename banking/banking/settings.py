"""
Django settings for GAX Banking project - Local Testing Configuration
"""

from pathlib import Path
import os
from decouple import config, Csv
from datetime import timedelta

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-test-key-for-local-development-only'
)
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv()
)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    # Local apps
    'accounts.apps.AccountsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.log_request.LogRequestMiddleware',
]

ROOT_URLCONF = 'banking.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'accounts' / 'templates',
        ],
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

WSGI_APPLICATION = 'banking.wsgi.application'

# Database - Using SQLite for easy local testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': (
        'rest_framework.pagination.PageNumberPagination'
    ),
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'sensitive': '10/minute',
        'payment': '50/hour',
    },
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_REFRESH_TOKEN_LIFETIME', default=1440, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True

# Caching - In-memory for local testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery Configuration - Disabled for simple testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email Configuration - Console backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Payment Mode Toggle
USE_LIVE_PAYMENT = config('USE_LIVE_PAYMENT', default=True, cast=bool)

# Paystack Configuration (PRIMARY PAYMENT GATEWAY)
PAYSTACK_LIVE_SECRET_KEY = config(
    'PAYSTACK_LIVE_SECRET_KEY',
    default='sk_live_placeholder'
)
PAYSTACK_LIVE_PUBLIC_KEY = config(
    'PAYSTACK_LIVE_PUBLIC_KEY',
    default='pk_live_placeholder'
)
PAYSTACK_BASE_URL = config(
    'PAYSTACK_BASE_URL',
    default='https://api.paystack.co'
)

# Moniepoint Configuration (BACKUP)
MONIEPOINT_SANDBOX_BASE_URL = config(
    'MONIEPOINT_SANDBOX_BASE_URL',
    default='https://sandbox.moniepoint.com'
)
MONIEPOINT_SANDBOX_API_KEY = config(
    'MONIEPOINT_SANDBOX_API_KEY',
    default='test-api-key'
)
MONIEPOINT_SANDBOX_SECRET_KEY = config(
    'MONIEPOINT_SANDBOX_SECRET_KEY',
    default='test-secret-key'
)
MONIEPOINT_SANDBOX_CONTRACT_CODE = config(
    'MONIEPOINT_SANDBOX_CONTRACT_CODE',
    default='test-contract'
)
MONIEPOINT_SANDBOX_CLIENT_ID = config(
    'MONIEPOINT_SANDBOX_CLIENT_ID',
    default='test-client-id'
)

# Moniepoint Live Configuration
MONIEPOINT_LIVE_BASE_URL = config(
    'MONIEPOINT_LIVE_BASE_URL',
    default='https://api.moniepoint.com'
)
MONIEPOINT_LIVE_API_KEY = config(
    'MONIEPOINT_LIVE_API_KEY',
    default='live-api-key'
)
MONIEPOINT_LIVE_SECRET_KEY = config(
    'MONIEPOINT_LIVE_SECRET_KEY',
    default='live-secret-key'
)
MONIEPOINT_LIVE_CONTRACT_CODE = config(
    'MONIEPOINT_LIVE_CONTRACT_CODE',
    default='live-contract'
)
MONIEPOINT_LIVE_CLIENT_ID = config(
    'MONIEPOINT_LIVE_CLIENT_ID',
    default='live-client-id'
)

# Bill Payment Configuration
BILL_PAYMENT_API_URL = config(
    'BILL_PAYMENT_API_URL',
    default='https://api.billpayment.com'
)
BILL_PAYMENT_API_KEY = config(
    'BILL_PAYMENT_API_KEY',
    default='test-api-key'
)

# Stripe Configuration - COMMENTED OUT (Using Moniepoint)
# STRIPE_PUBLIC_KEY = config(
#     'STRIPE_PUBLIC_KEY',
#     default='pk_test_placeholder'
# )
# STRIPE_SECRET_KEY = config(
#     'STRIPE_SECRET_KEY',
#     default='sk_test_placeholder'
# )

# Security Settings (relaxed for local testing)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}



