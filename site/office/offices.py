from django.template.loader import render_to_string
from django.utils.functional import cached_property

from churchcal.calculations import get_calendar_date


class OfficeSection(object):
    def __init__(self, date):
        self.date = date

    @cached_property
    def data(self):
        raise NotImplementedError


class EPHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Evening Prayer"}


class EPCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Commemorations"}


# ==== Offices


class Office(object):

    name = "Daily Office"
    modules = []

    def __init__(self, date):
        self.date = get_calendar_date(date)

    def render(self):
        rendering = ""
        for module, template in self.modules:
            rendering += render_to_string(template, module(self.date).data)
        return rendering


class EveningPrayer(Office):

    name = "Evening Prayer"
    modules = [
        (EPHeading, "office/evening_prayer/heading.html"),
        (EPCommemorationListing, "office/evening_prayer/commemoration_listing.html"),
    ]
