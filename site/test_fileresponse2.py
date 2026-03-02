import os
import django
from django.conf import settings
from django.http import FileResponse

settings.configure(
    DEBUG=True,
    SECRET_KEY="secret",
    ROOT_URLCONF=__name__,
    MIDDLEWARE_CLASSES=(),
)
django.setup()

with open("test_0.mp3", "wb") as f:
    pass

f = open("test_0.mp3", "rb")
response = FileResponse(f, content_type="audio/mpeg")


class MockRequest:
    method = "GET"
    META = {"HTTP_RANGE": "bytes=0-"}


# In Django, FileResponse evaluates the range during __iter__ or when setting headers.
# Let's just use the middleware or call set_headers
response.set_headers(None)
print("Status before:", response.status_code)
# Actually, Django's CommonMiddleware or FileResponse itself handles it?
# Let's check FileResponse source.
