"""
URL routing for RSS and Atom feeds
"""

from django.urls import path
from .feeds import DailyOfficeRSSFeed, DailyOfficeAtomFeed

app_name = 'feeds'

urlpatterns = [
    path('feed.rss', DailyOfficeRSSFeed(), name='rss'),
    path('feed.atom', DailyOfficeAtomFeed(), name='atom'),
    path('feed/', DailyOfficeRSSFeed(), name='default'),  # Default to RSS
]
