from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from churchcal.calculations import ChurchYear
from office.offices import EveningPrayer, MorningPrayer


def morning_prayer(request, year, month, day):
    mp = MorningPrayer("{}-{}-{}".format(year, month, day))
    return render(request, "office/office.html", {"office": mp})


def evening_prayer(request, year, month, day):
    ep = EveningPrayer("{}-{}-{}".format(year, month, day))
    return render(request, "office/office.html", {"office": ep})

def church_year(request, start_year):
    church_year = ChurchYear(start_year)
    return render(request, "office/church_year.html", {"start_year": start_year, "end_year": start_year + 1, "church_year": church_year})

def today_evening_prayer(request):
    return render(request, "office/evening_prayer/redirect.html", {})
