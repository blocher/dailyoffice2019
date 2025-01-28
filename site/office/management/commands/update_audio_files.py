from datetime import timedelta

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.urls import resolve
from django.utils import timezone


class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):

        now = timezone.now()
        start_date = now - timedelta(days=1)
        date_list = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(9)]

        for day in date_list:

            offices = [
                "office/morning_prayer",
                "office/midday_prayer",
                "office/evening_prayer",
                "office/compline",
                "family/morning_prayer/",
                "family/midday_prayer/",
                "family/early_evening_prayer",
                "family/close_of_day_prayer",
            ]

            for office in offices:

                # Create a mock GET request
                base_url = f"/api/v1/{office}/{day.strftime("%Y-%m-%d")}"

                # Define the query parameters as a dictionary
                query_params = {
                    "language_style": "contemporary",
                    "psalm_translation": "contemporary",
                    "bible_translation": "esv",
                    "psalter": "60",  # needed
                    "reading_cycle": "1",
                    "reading_length": "full",
                    "reading_audio": "off",
                    "canticle_rotation": "1979",  # needed
                    "psalm_style": "whole_verse",  # needed
                    "lectionary": "daily-office-readings",  # needed
                    "confession": "long-on-fast",
                    "absolution": "lay",  # needed
                    "morning_prayer_invitatory": "invitatory_traditional",  # needed
                    "reading_headings": "off",
                    "language_style_for_our_father": "traditional",
                    "national_holidays": "all",
                    "suffrages": "rotating",
                    "collects": "rotating",
                    "mp_great_litany": "mp_litany_on",
                    "ep_great_litany": "ep_litany_on",
                    "general_thanksgiving": "on",
                    "chrysostom": "on",
                    "grace": "rotating",
                    "o_antiphons": "literal",
                    "family_readings": "brief",
                    "family_reading_audio": "off",
                    "family_collect": "time_of_day",
                    "family-opening-sentence": "family-opening-sentence-fixed",
                    "family-creed": "family-creed-yes",
                    "extra_collects": "",
                    "include_audio_links": "true",
                }

                contemporary_and_traditional = [
                    {
                        "language_style": "contemporary",
                        "psalm_translation": "contemporary",
                        "bible_translation": "esv",
                        "language_style_for_our_father": "contemporary",
                    },
                    {
                        "language_style": "traditional",
                        "psalm_translation": "traditional",
                        "bible_translation": "kjv",
                        "language_style_for_our_father": "traditional",
                    },
                ]

                for style in contemporary_and_traditional:
                    new_params = query_params.copy()
                    new_params |= style
                    more_changes = [
                        {
                            "psalter": "30",
                        },
                        {
                            "canticle_rotation": "default",
                        },
                        {
                            "canticle_rotation": "2011",
                        },
                        {
                            "psalm_style": "half_verse",
                        },
                        {
                            "psalm_style": "unison",
                        },
                        {
                            "lectionary": "mass-readings",
                        },
                        {
                            "absolution": "priest",
                        },
                        {
                            "morning_prayer_invitatory": "invitatory_jubilate_on_feasts",
                        },
                        {
                            "morning_prayer_invitatory": "celebratory_always",
                        },
                        {
                            "morning_prayer_invitatory": "invitatory_rotating",
                        },
                    ]
                    for change in more_changes:
                        newest_params = new_params.copy()
                        newest_params |= change

                        # Create the mock request
                        factory = RequestFactory()
                        request = factory.get(base_url, data=newest_params)
                        print(base_url, newest_params)
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
