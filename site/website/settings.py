"""
Django settings for sermons project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import mimetypes
import os

import environ

env = environ.Env(
    DEBUG=(bool, False),
    DEBUG_DATES=(bool, False),
    USE_CALENDAR_CACHE=(bool, True),
    MODE=(str, "web"),
    SECURE_SSL_REDIRECT=(bool, False),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_USE_SSL=(bool, False),
)
environ.Env.read_env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_ADDRESS = env("SITE_ADDRESS")

# Quick-start development settings - unsuitable for production
# See https://docs.djwebangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "TESTKEY")

SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", env("SECURE_PROXY_SSL_HEADER"))

# SECURITY WARNING: d
# Don't run with debug turned on in production!
DEBUG = env("DEBUG")
DEBUG_DATES = env("DEBUG_DATES")
USE_CALENDAR_CACHE = env("USE_CALENDAR_CACHE")
MODE = env("MODE")
APP_VERSION = 1.1

ALLOWED_HOSTS = [
    "*",
    "127.0.0.1:8000",
    "127.0.0.1",
    "dailyoffice2019.com",
    "www.dailyoffice2019.com",
    "api.dailyoffice2019.com",
    "data.dailyoffice2019.com",
]

# Application definition

INSTALLED_APPS = [
    "mjml",
    "mathfilters",
    "drf_yasg",
    "corsheaders",
    "adminsortable2",
    "widget_tweaks",
    "django.contrib.admin",
    # "material.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "django_ckeditor_5",
    "django_extensions",
    "django_inlinecss",
    "kronos",
    "rest_framework",
    "website",
    # "sermons",
    "churchcal",
    "psalter",
    "bible",
    "meta",
    "office",
    "djrichtextfield",
    "taggit",
    # "address",
    "array_tags",
    "django_distill",
    "webpack_loader",
    "robots",
    "standrew",
]

if DEBUG:
    INSTALLED_APPS = ["debug_toolbar"] + INSTALLED_APPS

MIDDLEWARE = [
    "bugsnag.django.middleware.BugsnagMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

ROOT_URLCONF = "website.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "office.context_processors.settings",
            ]
        },
    }
]

WSGI_APPLICATION = "website.wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env("POSTGRES_NAME"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

INTERNAL_IPS = ["127.0.0.1"]
# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = BASE_DIR + "/uploads/"

MEDIA_URL = "/uploads/"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

SHELL_PLUS = "ipython"

JET_DEFAULT_THEME = "light-green"
JET_SIDE_MENU_COMPACT = True
JET_CHANGE_FORM_SIBLING_LINKS = True

JET_THEMES = [
    {
        "theme": "default",  # theme folder name
        "color": "#47bac1",  # color of the theme's button in user menu
        "title": "Default",  # theme title
    },
    {"theme": "green", "color": "#44b78b", "title": "Green"},
    {"theme": "light-green", "color": "#2faa60", "title": "Light Green"},
    {"theme": "light-violet", "color": "#a464c4", "title": "Light Violet"},
    {"theme": "light-blue", "color": "#5EADDE", "title": "Light Blue"},
    {"theme": "light-gray", "color": "#222", "title": "Light Gray"},
]

DJRICHTEXTFIELD_CONFIG = {
    "js": ["//cdn.tinymce.com/4/tinymce.min.js"],
    "init_template": "djrichtextfield/init/tinymce.js",
    "settings": {
        "menubar": True,
        "toolbar": "formatselect | bold italic strikethrough forecolor backcolor permanentpen formatpainter | link image media pageembed | alignleft aligncenter alignright alignjustify  | numlist bullist outdent indent | removeformat | addcomment",
        "width": "100%",
        "height": 800,
    },
}

GOOGLE_API_KEY = env("GOOGLE_API_KEY")
GOOGLE_CUSTOM_SEARCH_ENGINE_KEY = env("GOOGLE_CUSTOM_SEARCH_ENGINE_KEY")


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": show_toolbar}

DISTILL_DIR = "{}/../static_export".format(BASE_DIR)

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": False,
        "BUNDLE_DIR_NAME": "office/js/",  # must end with slash
        "STATS_FILE": os.path.join(BASE_DIR, "webpack-stats.json"),
        "POLL_INTERVAL": 0.1,
        "TIMEOUT": None,
        "IGNORE": [r".+\.hot-update.js", r".+\.map"],
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SITE_ID = 1

FIRST_BEGINNING_YEAR = int(env("FIRST_BEGINNING_YEAR"))
LAST_BEGINNING_YEAR = int(env("LAST_BEGINNING_YEAR"))

FIRST_BEGINNING_YEAR_APP = int(env("FIRST_BEGINNING_YEAR_APP"))
LAST_BEGINNING_YEAR_APP = int(env("LAST_BEGINNING_YEAR_APP"))

META_SITE_PROTOCOL = "https"
META_SITE_DOMAIN = "www.dailyoffice2019.com"
META_SITE_TYPE = "website"
META_SITE_NAME = "The Daily Office"
META_DEFAULT_KEYWORDS = [
    "daily office",
    "prayer",
    "divine office",
    "daily prayer",
    "evening prayer",
    "morning prayer",
    "compline",
    "midday prayer",
    "noonday prayer",
    "nones",
    "matins",
    "vespers",
    "evensong",
    "liturgy of the hours",
    "breviary",
    "anglican",
    "episcopal",
    "Anglican Church in North America",
    "ACNA",
    "common prayer",
    "book of common prayer",
    "bcp",
    "2019",
]
META_USE_OG_PROPERTIES = True
META_USE_TWITTER_PROPERTIES = True
META_USE_GOOGLEPLUS_PROPERTIES = True
META_USE_TITLE_TAG = True
META_SITE_TYPE = "website"
META_FB_APPID = "826553607777260"
META_FB_AUTHOR_URL = "https://www.dailyoffice2019.com"
META_TWITTER_AUTHOR = "Daily Office, Book of Common Prayer 2019"
META_TWITTER_SITE = "https://www.dailyoffice2019.com"
META_OG_SECURE_URL_ITEMS = []

ROBOTS_SITEMAP_URLS = ["https://www.dailyoffice2019.com/sitemap.xml"]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"]
}
# IS this right?

CORS_ALLOW_ALL_ORIGINS = True
mimetypes.add_type("image/svg+xml", ".svg", True)

SWAGGER_SETTINGS = {"USE_SESSION_AUTH": False}

BUGSNAG = {"api_key": env("BUGSNAG_KEY"), "project_root": BASE_DIR}

DEFAULT_FROM_EMAIL = "donotreply@mail.dailyoffice2019.com"
DEFAULT_REPLY_TO_EMAIL = "feedback@dailyoffice2019.com"
MAILGUN_DOMAIN = "mail.dailyoffice2019.com"
MAILGUN_PUBLIC_KEY = env("MAILGUN_PUBLIC_KEY")
MAILGUN_PRIVATE_KEY = env("MAILGUN_PRIVATE_KEY")

DEF_TEMPLATES_SOURCE_PATH = "templates_sources"
DEF_TEMPLATES_TARGET_PATH = "app/standrew/templates/emails_app"
DEF_STATIC_TARGET_PATH = "app/static/emails_app"

MJML_BACKEND_MODE = "httpserver"
MJML_HTTPSERVERS = [
    {
        "URL": "https://api.mjml.io/v1/render",  # official MJML API
        "HTTP_AUTH": (env("MJML_APPLICATION_ID"), env("MJML_SECRET_KEY")),
    },
]

ZOOM_LINK = env("ZOOM_LINK")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")  # 'smtp.gmail.com'
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_USE_SSL = env("EMAIL_USE_SSL")  # False
EMAIL_PORT = env("EMAIL_PORT")  # 587
EMAIL_HOST_USER = env("EMAIL_HOST_USER")  # 587
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")  # 587

OPENAI_API_KEY = env("OPENAI_API_KEY")

OMDB_API_KEY = env("OMDB_API_KEY")
UTELLY_API_KEY = env("UTELLY_API_KEY")
IMDB_API_KEY = env("IMDB_API_KEY")
YOUTUBE_API_KEY = env("YOUTUBE_API_KEY")

MAILCHIMP_API_KEY = env("MAILCHIMP_API_KEY")
MAILCHIMP_PREFIX = env("MAILCHIMP_PREFIX")
MAILCHIMP_LIST_ID = env("MAILCHIMP_LIST_ID")

OPENVERSE_CLIENT_ID = env("OPENVERSE_CLIENT_ID")
OPENVERSE_CLIENT_SECRET = env("OPENVERSE_CLIENT_SECRET")
PERPLEXITY_API_KEY = env("PERPLEXITY_API_KEY")

customColorPalette = [
    {"color": "hsl(4, 90%, 58%)", "label": "Red"},
    {"color": "hsl(340, 82%, 52%)", "label": "Pink"},
    {"color": "hsl(291, 64%, 42%)", "label": "Purple"},
    {"color": "hsl(262, 52%, 47%)", "label": "Deep Purple"},
    {"color": "hsl(231, 48%, 48%)", "label": "Indigo"},
    {"color": "hsl(207, 90%, 54%)", "label": "Blue"},
]

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "imageUpload",
        ],
    },
    "extends": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
        ],
        "toolbar": [
            "heading",
            "|",
            "outdent",
            "indent",
            "|",
            "bold",
            "italic",
            "link",
            "underline",
            "strikethrough",
            "code",
            "subscript",
            "superscript",
            "highlight",
            "|",
            "codeBlock",
            "sourceEditing",
            "insertImage",
            "bulletedList",
            "numberedList",
            "todoList",
            "|",
            "blockQuote",
            "imageUpload",
            "|",
            "fontSize",
            "fontFamily",
            "fontColor",
            "fontBackgroundColor",
            "mediaEmbed",
            "removeFormat",
            "insertTable",
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "|",
                "imageStyle:alignLeft",
                "imageStyle:alignRight",
                "imageStyle:alignCenter",
                "imageStyle:side",
                "|",
            ],
            "styles": [
                "full",
                "side",
                "alignLeft",
                "alignRight",
                "alignCenter",
            ],
        },
        "table": {
            "contentToolbar": ["tableColumn", "tableRow", "mergeTableCells", "tableProperties", "tableCellProperties"],
            "tableProperties": {"borderColors": customColorPalette, "backgroundColors": customColorPalette},
            "tableCellProperties": {"borderColors": customColorPalette, "backgroundColors": customColorPalette},
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading1", "view": "h1", "title": "Heading 1", "class": "ck-heading_heading1"},
                {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
            ]
        },
    },
    "list": {
        "properties": {
            "styles": "true",
            "startIndex": "true",
            "reversed": "true",
        }
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    },
}

# Configure Django storage to use Backblaze B2 via django-storages
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": env("STORAGES_ACCESS_KEY_ID"),
            "secret_key": env("STORAGES_SECRET_ACCESS_KEY"),
            "bucket_name": env("STORAGES_BUCKET_NAME"),
            "endpoint_url": env("STORAGES_ENDPOINT_URL", default="https://s3.us-west-004.backblazeb2.com"),
            "region_name": env("STORAGES_REGION_NAME", default="us-west-004"),
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
