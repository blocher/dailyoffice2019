from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from office.offices import EveningPrayer, MorningPrayer


def morning_prayer(request, year, month, day):
    mp = MorningPrayer("{}-{}-{}".format(year, month, day))
    footer_links = {}
    return render(request, "office/office.html", {"office": mp})


def evening_prayer(request, year, month, day):
    ep = EveningPrayer("{}-{}-{}".format(year, month, day))
    footer_links = {}
    return render(request, "office/office.html", {"office": ep})


def today_evening_prayer(request):
    return render(request, "office/evening_prayer/redirect.html", {})
