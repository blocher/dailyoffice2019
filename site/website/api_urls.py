from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework import routers

from churchcal.api.views import DayView, MonthView, YearView
from office.api.views.index import (
    MorningPrayerView,
    AvailableSettings,
    MorningPrayerDisplayView,
    EveningPrayerView,
    MiddayPrayerView,
    EmailSignupView,
    ComplineView,
    FamilyMorningPrayerView,
    FamilyMiddayPrayerView,
    FamilyEarlyEveningPrayerView,
    FamilyCloseOfDayPrayerView,
    ReadingsView,
    GreatLitanyView,
)
from office.api.views.resources import (
    CollectsViewSet,
    PsalmsViewSet,
    AboutViewSet,
    CollectCategoryViewSet,
    ScriptureViewSet,
    GroupedCollectsViewSet,
)

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
router_v1.register(r"psalms", PsalmsViewSet, basename="psalms")
router_v1.register(r"scripture", ScriptureViewSet, basename="scripture2")

router_v1.register(r"collect_categories", CollectCategoryViewSet, basename="collect_category")

urlpatterns = [
    re_path(r"^api/v1/", include(router_v1.urls)),
    path("api/v1/api-auth/", include("rest_framework.urls")),
    path(r"api/v1/calendar/<int:year>-<int:month>-<int:day>", DayView.as_view(), name="day_view"),
    path(r"api/v1/readings/<int:year>-<int:month>-<int:day>", ReadingsView.as_view(), name="readings"),
    path(r"api/v1/litany", GreatLitanyView.as_view(), name="litany"),
    path(r"api/v1/calendar/<int:year>-<int:month>", MonthView.as_view(), name="month_view"),
    path(r"api/v1/calendar/<int:year>", YearView.as_view(), name="month_view"),
    path(
        r"api/v1/office/morning_prayer/<int:year>-<int:month>-<int:day>",
        MorningPrayerView.as_view(),
        name="morning_prayer_view",
    ),
    path(
        r"api/v1/office/evening_prayer/<int:year>-<int:month>-<int:day>",
        EveningPrayerView.as_view(),
        name="evening_prayer_view",
    ),
    path(
        r"api/v1/office/midday_prayer/<int:year>-<int:month>-<int:day>",
        MiddayPrayerView.as_view(),
        name="midday_view",
    ),
    path(
        r"api/v1/office/compline/<int:year>-<int:month>-<int:day>",
        ComplineView.as_view(),
        name="compline_view",
    ),
    path(
        r"api/v1/family/morning_prayer/<int:year>-<int:month>-<int:day>",
        FamilyMorningPrayerView.as_view(),
        name="family_morning_prayer_view",
    ),
    path(
        r"api/v1/family/early_evening_prayer/<int:year>-<int:month>-<int:day>",
        FamilyEarlyEveningPrayerView.as_view(),
        name="family_early_evening_prayer_view",
    ),
    path(
        r"api/v1/family/midday_prayer/<int:year>-<int:month>-<int:day>",
        FamilyMiddayPrayerView.as_view(),
        name="family_midday_view",
    ),
    path(
        r"api/v1/family/close_of_day_prayer/<int:year>-<int:month>-<int:day>",
        FamilyCloseOfDayPrayerView.as_view(),
        name="family_close_of_day_view",
    ),
    path(
        r"api/v1/collects",
        CollectsViewSet.as_view({"get": "list"}),
        name="collects_view",
    ),
    path(
        r"api/v1/grouped_collects",
        GroupedCollectsViewSet.as_view({"get": "list"}),
        name="grouped_collects_view",
    ),
    path(
        r"api/v1/about",
        AboutViewSet.as_view({"get": "list"}),
        name="about_view",
    ),
    path(
        r"api/v1/email_signup",
        EmailSignupView.as_view(),
        name="email_signup",
    ),
    path(
        r"new/office/morning_prayer/<int:year>-<int:month>-<int:day>",
        MorningPrayerDisplayView.as_view(),
        name="morning_prayer_display_view",
    ),
    re_path(r"^api/openapi(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    re_path(r"^api/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    re_path(r"^api/redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
