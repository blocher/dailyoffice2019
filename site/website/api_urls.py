from django.conf.urls import url
from rest_framework import routers
from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from churchcal.api.views import DayView, MonthView, YearView
from office.api.views import MorningPrayerView, MorningPrayerDisplayView, AvailableSettings

schema_view = get_schema_view(
    openapi.Info(
        title="Daily Office 2019 API",
        default_version="v1",
        description="API for accessing calendar and daily prayer in JSON format",
        terms_of_service="https://www.dailyoffice2019.com/privacy-policy/",
        contact=openapi.Contact(email="feedback@dailyoffice2019.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router_v1 = routers.DefaultRouter()
router_v1.register(r"available_settings", AvailableSettings)

urlpatterns = [
    re_path(r"^api/v1/", include(router_v1.urls)),
    path("api/v1/api-auth/", include("rest_framework.urls")),
    path(r"api/v1/calendar/<int:year>-<int:month>-<int:day>", DayView.as_view(), name="day_view"),
    path(r"api/v1/calendar/<int:year>-<int:month>", MonthView.as_view(), name="month_view"),
    path(r"api/v1/calendar/<int:year>", YearView.as_view(), name="month_view"),
    path(
        r"api/v1/office/morning_prayer/<int:year>-<int:month>-<int:day>",
        MorningPrayerView.as_view(),
        name="morning_prayer_view",
    ),
    path(
        r"new/office/morning_prayer/<int:year>-<int:month>-<int:day>",
        MorningPrayerDisplayView.as_view(),
        name="morning_prayer_display_view",
    ),
    url(r"^api/openapi(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    url(r"^api/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    url(r"^api/redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
