from django.urls import path

from patrons import views


app_name = "patrons"

urlpatterns = [
    path("", views.index, name="index"),
    path("feasts/<int:pk>/", views.feast_detail, name="feast_detail"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("calendar/<str:token>.ics", views.calendar_feed, name="calendar_feed"),
]
