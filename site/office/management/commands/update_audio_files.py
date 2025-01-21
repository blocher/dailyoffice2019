from datetime import timedelta

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.urls import resolve
from django.utils import timezone


class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        # Create a RequestFactory instance
        factory = RequestFactory()

        now = timezone.now()
        start_date = now - timedelta(days=1)
        date_list = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

        # Create a mock GET request
        base_url = "/api/v1/office/evening_prayer/2025-1-20"

        # Define the query parameters as a dictionary
        query_params = {
            "language_style": "contemporary",
            "psalm_translation": "contemporary",
            "bible_translation": "esv",
            "psalter": "60",
            "reading_cycle": "1",
            "reading_length": "full",
            "reading_audio": "off",
            "canticle_rotation": "1979",
            "psalm_style": "whole_verse",
            "lectionary": "daily-office-readings",
            "confession": "long-on-fast",
            "absolution": "lay",
            "morning_prayer_invitatory": "invitatory_traditional",
            "reading_headings": "off",
            "language_style_for_our_father": "traditional",
            "national_holidays": "all",
            "suffrages": "rotating",
            "collects": "rotating",
            "mp_great_litany": "mp_litany_off",
            "ep_great_litany": "ep_litany_off",
            "general_thanksgiving": "on",
            "chrysostom": "on",
            "grace": "rotating",
            "o_antiphons": "literal",
            "family_readings": "long",
            "family_reading_audio": "off",
            "family_collect": "time_of_day",
            "family-opening-sentence": "family-opening-sentence-fixed",
            "family-creed": "family-creed-no",
            "extra_collects": "",
            "include_audio_links": "true",
        }

        # Create the mock request
        factory = RequestFactory()
        request = factory.get(base_url, data=query_params)
        # Resolve the view based on the URL
        match = resolve(base_url)

        # Call the resolved view with the mock request
        response = match.func(request, *match.args, **match.kwargs)

        # Check if the response is a TemplateResponse
        if hasattr(response, "render") and callable(response.render):
            response = response.render()  # Render the TemplateResponse explicitly

        # Print the response content
        print(response.content)
        print(response.status_code)
