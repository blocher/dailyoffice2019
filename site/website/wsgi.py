"""
WSGI config for sermons project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import time
import traceback
import signal
import sys

from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

sys.path.append("/var/www/dailyoffice2019/site")
sys.path.append("/var/www/dailyoffice2019/env/lib/python3.8/site-packages")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")


try:
    application = get_wsgi_application()
except Exception:
    # Error loading applications
    if "mod_wsgi" in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)
