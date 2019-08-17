"""sermons URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from sermons import views as sermon_views


urlpatterns = [
    path("sermons", sermon_views.sermons, name="sermons"),
    path("sermon/<uuid:id>", sermon_views.sermon, name="sermon"),
    path("djrichtextfield/", include("djrichtextfield.urls")),
    path("jet/", include("jet.urls", "jet")),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

admin.site.site_title = "Sermon Database"
admin.site.site_header = "Sermon Database Administration"
admin.site.index_title = "Sermon Database Administration"

handler404 = "sermons.views.handle404"
