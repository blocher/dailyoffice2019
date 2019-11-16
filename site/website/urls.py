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
import datetime

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from sermons import views as sermon_views
from django_distill import distill_path
from office import views as office_views

from django.contrib.staticfiles.templatetags.staticfiles import static as staticfiles
from django.urls import path, include
from django.utils.translation import ugettext_lazy as _

from material.admin.sites import site

from office.views import evening_prayer

site.site_header = _("Elizabeth Locher's Sermon Archive")
site.site_title = _("Elizabeth Locher's Sermon Archive")
# site.favicon = staticfiles('path/to/favicon')


def get_today_evening_prayer():
    return None


def get_evening_prayer_days():

    days_back = 365 * 2
    days_forward = 365 * 2

    base = datetime.datetime.today()
    previous_date_list = [base - datetime.timedelta(days=x) for x in range(days_back)]
    future_date_list = [base + datetime.timedelta(days=x) for x in range(days_forward)]
    date_list = previous_date_list + future_date_list
    for date in date_list:
        yield {"year": date.year, "month": date.month, "day": date.day}

def get_church_years():

    for year in [2017, 2018, 2019, 2020, 2021, 2022]:
        yield {"start_year": year, "end_year": year+1}


urlpatterns = [
    path("sermons", sermon_views.sermons, name="sermons"),
    path("sermon/<uuid:id>", sermon_views.sermon, name="sermon"),
    path("djrichtextfield/", include("djrichtextfield.urls")),
    # path("jet/", include("jet.urls", "jet")),
    # path("admin/", admin.site.urls),
    path("admin/", include("material.admin.urls")),
    distill_path(
        "office/evening_prayer/<int:year>-<int:month>-<int:day>/",
        office_views.evening_prayer,
        name="evening_prayer",
        distill_func=get_evening_prayer_days,
    ),
    distill_path(
        "office/morning_prayer/<int:year>-<int:month>-<int:day>/",
        office_views.morning_prayer,
        name="morning_prayer",
        distill_func=get_evening_prayer_days,
    ),
      distill_path(
          "office/church_year/<int:start_year>-<int:end_year>",
          office_views.church_year,
          name="church_year",
          distill_func=get_church_years,
      ),
    distill_path(
        "", office_views.today_evening_prayer, name="today_evening_prayer", distill_func=get_today_evening_prayer
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

admin.site.site_title = "Sermon Database"
admin.site.site_header = "Sermon Database Administration"
admin.site.index_title = "Sermon Database Administration"

handler404 = "sermons.views.handle404"
