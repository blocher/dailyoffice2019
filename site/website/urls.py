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
from datetime import date

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django_distill import distill_path
from future.backports.datetime import timedelta
from material.admin.sites import site

from django.contrib.sitemaps import views

from churchcal.calculations import ChurchYear
from office import views as office_views
# from sermons import views as sermon_views
from django.contrib.sitemaps import Sitemap
# site.site_header = _("Elizabeth Locher's Sermon Archive")
# site.site_title = _("Elizabeth Locher's Sermon Archive")
# site.favicon = staticfiles('path/to/favicon')
from django.views.static import serve

def get_about():
    return None

def get_now():
    return None

def get_none():
    return None

def get_days():
    date_list = []
    for year in get_church_years():
        church_year = ChurchYear(year["start_year"])
        for day in church_year:
            date_list.append(day.date)
    for date in date_list:
        yield {"year": date.year, "month": date.month, "day": date.day}

def get_church_years():

    for year in range(settings.FIRST_BEGINNING_YEAR, settings.LAST_BEGINNING_YEAR + 1):
        yield {"start_year": year, "end_year": year+1}

class MorningPrayerSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7
    protocol = "https"

    def items(self):
        days = []
        for day in get_days():
            days.append(day)
        return days

    def lastmod(self, obj):
        return date.today()

    def location(self, obj):
        return '/morning_prayer/{}-{}-{}'.format(obj['year'], obj['month'], obj['day']);

class MiddayPrayerSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = "https"

    def items(self):
        days = []
        for day in get_days():
            days.append(day)
        return days

    def lastmod(self, obj):
        return date.today()

    def location(self, obj):
        return '/midday_prayer/{}-{}-{}'.format(obj['year'], obj['month'], obj['day']);

class EveningPrayerSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7
    protocol = "https"

    def items(self):
        days = []
        for day in get_days():
            days.append(day)
        return days

    def lastmod(self, obj):
        return date.today()

    def location(self, obj):
        return '/evening_prayer/{}-{}-{}'.format(obj['year'], obj['month'], obj['day']);

class ComplineSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = "https"

    def items(self):
        days = []
        for day in get_days():
            days.append(day)
        return days

    def lastmod(self, obj):
        return date.today()

    def location(self, obj):
        return '/compline/{}-{}-{}'.format(obj['year'], obj['month'], obj['day']);

class CalendarSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = "https"

    def items(self):
        years = []
        for year in get_church_years():
            print(year)
            years.append(year)
        return years

    def lastmod(self, obj):
        return date.today()

    def location(self, obj):
        return '/church_year/{}-{}'.format(obj['start_year'], obj['end_year']);

class SettingsSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.3
    protocol = "https"

    def items(self):
        return ['settings']

    def lastmod(self, obj):
        return date.today()

    def location(self, obj):
        return '/{}'.format(obj);

class AboutSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    protocol = "https"

    def items(self):
        return ['about']

    def lastmod(self, obj):
        return date.today()

    def location(self, obj):
        return '/{}'.format(obj);

class HomeSitemap(Sitemap):
    changefreq = "always"
    priority = 1.0
    protocol = "https"

    def items(self):
        return ['home']

    def lastmod(self, obj):
        return False

    def location(self, obj):
        return '/';

sitemaps = {
    'morning_prayer': MorningPrayerSitemap(),
    'midday_prayer': MiddayPrayerSitemap(),
    'evening_prayer': EveningPrayerSitemap(),
    'compline': ComplineSitemap(),
    'calendar': CalendarSitemap(),
    'settings': SettingsSitemap(),
    'about': AboutSitemap(),
    'home': HomeSitemap(),
}

def get_distill_sitemap():

    yield None

def sitemap_index_view(request):
    return views.index(request, sitemaps)

def sitemap_view(request):
    return views.sitemap(request, sitemaps)



urlpatterns = [
    # path("sermons", sermon_views.sermons, name="sermons"),
    # path("sermon/<uuid:id>", sermon_views.sermon, name="sermon"),
    # path("djrichtextfield/", include("djrichtextfield.urls")),
    # path("jet/", include("jet.urls", "jet")),
    # path("admin/", admin.site.urls),
    # path("admin/", include("material.admin.urls")),
    distill_path(
        "evening_prayer/<int:year>-<int:month>-<int:day>/",
        office_views.evening_prayer,
        name="evening_prayer",
        distill_func=get_days,
    ),
      distill_path(
          "midday_prayer/<int:year>-<int:month>-<int:day>/",
          office_views.midday_prayer,
          name="midday_prayer",
          distill_func=get_days,
      ),
    distill_path(
        "morning_prayer/<int:year>-<int:month>-<int:day>/",
        office_views.morning_prayer,
        name="morning_prayer",
        distill_func=get_days,
    ),
      distill_path(
          "compline/<int:year>-<int:month>-<int:day>/",
          office_views.compline,
          name="compline",
          distill_func=get_days,
      ),
    distill_path(
          "church_year/<int:start_year>-<int:end_year>/",
          office_views.church_year,
          name="church_year",
          distill_func=get_church_years,
      ),
      distill_path(
          "about/",
          office_views.about,
          name="about",
          distill_func=get_about,
      ),
    distill_path(
          "settings/",
          office_views.settings,
          name="settings",
          distill_func=get_about,
      ),
    distill_path(
          "signup-thank-you/",
          office_views.signup_thank_you,
          name="signup_thank_you",
          distill_func=get_none,
      ),
    distill_path(
        "", office_views.now, distill_file="index.html", name="now", distill_func=get_now
    ),
    distill_path('sitemap.xml', sitemap_view,
         name='django.contrib.sitemaps.views.sitemap', distill_func=get_distill_sitemap),
    distill_path('404.html', office_views.four_oh_four, name='404', distill_func=get_none),
    distill_path('robots.txt', TemplateView.as_view(template_name="office/robots.txt", content_type='text/plain'), name="robots", distill_func=get_none)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
#
# admin.site.site_title = "Sermon Database"
# admin.site.site_header = "Sermon Database Administration"
# admin.site.index_title = "Sermon Database Administration"

# handler404 = "sermons.views.handle404"
