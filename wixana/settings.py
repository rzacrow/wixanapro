from pathlib import Path
import os
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.conf.urls.static import static
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8_+*_os2v!=$iuph*9hys-fld@arnb2ilnyuu#t&$nv2z@m)a0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['django-app']

#User model
AUTH_USER_MODEL = 'accounts.User'

# Application definition

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'gamesplayed',
    "bootstrap_datepicker_plus",

]

MIDDLEWARE = [
    "django.middleware.csrf.CsrfViewMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wixana.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'wixana.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE-NAME', 'wixana'),
        'USER': os.environ.get('DATABASE-USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE-PASSWORD', 'Reza2001'),
        'HOST': os.environ.get('DATABASE-HOST', 'database'),
        'PORT': os.environ.get('DATABASE-PORT', '5432')
    }
}

CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ["https://wixana.ir", "https://*.wixana.ir", "https://*.wixana.ir", "https://www.wixana.ir"]

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tehran'
DATETIME_FORMAT="%Y-%m-%d %H:%M"
DATETIME_INPUT_FORMATS =  ['%Y-%m-%d %H:%M']

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIR = [
    os.path.join(BASE_DIR, 'static/')
]

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


UNFOLD = {
    "SITE_TITLE": "Wixana",
    "SITE_HEADER": "Wixana",
    
    "SIDEBAR": {
        "show_search": False,  # Search in applications and models names
        "show_all_applications": False,  # Dropdown with all applications and models
        "STYLES": [
            lambda request: static("css/style.css"),
        ],
        "SCRIPTS": [
            lambda request: static("js/script.js"),
            lambda request: BASE_DIR  / "accounts/js/attendance.js",
        ],
        "navigation": [
            {
                "title": _("Menu"),
                "separator": True,  # Top border
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": _("Alts"),
                        "icon": "chess",
                        "link": reverse_lazy("admin:accounts_alt_changelist"),
                    },
                    {
                        "title": _("Teams"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:accounts_team_changelist"),
                    },
                    {
                        "title": _("Realms"),
                        "icon": "savings",
                        "link": reverse_lazy("admin:accounts_realm_changelist"),
                    },
                    {
                        "title": _("Cycle"),
                        "icon": "sports",
                        "link": reverse_lazy("admin:gamesplayed_cycle_changelist"),
                    },
                    #{
                    #    "title": _("Attendance"),
                    #    "icon": "note_stack_add",
                    #    "badge": "@",
                    #    "link": reverse_lazy("admin:gamesplayed_attendance_changelist"),
                    #},
                    {
                        "title": _("Payments"),
                        "icon": "point_of_sale",
                        "link": reverse_lazy("admin:gamesplayed_payment_changelist"),
                    },
                    {
                        "title": _("User Wallet"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:accounts_wallet_changelist"),
                    },
                    {
                        "title": _("Roles"),
                        "icon": "checklist",
                        "link": reverse_lazy("admin:gamesplayed_role_changelist"),
                    },
                    {
                        "title": _("Run type"),
                        "icon": "extension",
                        "link": reverse_lazy("admin:gamesplayed_runtype_changelist"),
                    },
                    {
                        "title": _("Transaction"),
                        "icon": "credit_score",
                        "link": reverse_lazy("admin:accounts_transaction_changelist"),
                    },
                    {
                        "title": _("Loan"),
                        "icon": "account_balance",
                        "link": reverse_lazy("admin:accounts_loan_changelist"),
                    },
                    {
                        "title": _("Loan repayment"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:accounts_paymentdebttrackingcode_changelist"),
                    },
                    {
                        "title": _("Debtors"),
                        "icon": "order_play",
                        "link": reverse_lazy("admin:accounts_debt_changelist"),
                    },
                    {
                        "title": _("Cut in IR"),
                        "icon": "currency_exchange",
                        "link": reverse_lazy("admin:gamesplayed_cutinir_changelist"),
                    },
                    {
                        "title": _("Ticket"),
                        "icon": "mail",
                        "link": reverse_lazy("admin:accounts_ticket_changelist"),
                    },
                ],
            },
        ],
    },
}



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.wixana.ir'
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'support@wixana.ir'
EMAIL_HOST_PASSWORD = 'd#MXOsG-&OML'
