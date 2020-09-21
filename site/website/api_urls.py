from rest_framework import routers
from django.urls import include, path, re_path
from rest_framework import routers

from churchcal.api.views import DayView

router_v1 = routers.DefaultRouter()

urlpatterns = [
    re_path(r"^api/v1/", include(router_v1.urls)),
    path('api/v1/api-auth/', include('rest_framework.urls')),
    path(r"api/v1/calendar/<int:year>-<int:month>-<int:day>", DayView.as_view(), name="day_view"),
]
