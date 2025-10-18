"""
URL routing for RSS and Atom feeds
"""

from django.urls import path
from .feeds import DailyOfficeRSSFeed

app_name = 'feeds'

urlpatterns = [
    path('feed/readings/30-day', DailyOfficeRSSFeed(psalter_cycle=30), name='readings_30_day'),
    path('feed/readings/60-day', DailyOfficeRSSFeed(psalter_cycle=60), name='readings_60_day'),
]
