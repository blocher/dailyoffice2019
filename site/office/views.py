from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from churchcal.calculations import ChurchYear
from churchcal.models import Season
from office.offices import EveningPrayer, MorningPrayer, Compline, MiddayPrayer


def morning_prayer(request, year, month, day):
    mp = MorningPrayer("{}-{}-{}".format(year, month, day))
    return render(request, "office/office.html", {"office": mp})

def evening_prayer(request, year, month, day):
    ep = EveningPrayer("{}-{}-{}".format(year, month, day))
    return render(request, "office/office.html", {"office": ep})

def compline(request, year, month, day):
    cp = Compline("{}-{}-{}".format(year, month, day))
    return render(request, "office/office.html", {"office": cp})

def midday_prayer(request, year, month, day):
    md = MiddayPrayer("{}-{}-{}".format(year, month, day))
    return render(request, "office/office.html", {"office": md})

def settings(request):
    return render(request, "office/settings.html", {})

def church_year(request, start_year, end_year=None):
    church_year = ChurchYear(start_year)
    months = []
    for date_str, date in church_year.dates.items():
        month = date.date.strftime("%b %Y")
        if month not in months:
            months.append(month)

    seasons = Season.objects.filter(calendar__abbreviation="ACNA_BCP2019").order_by("order").all()
    return render(request, "office/church_year.html", {"start_year": start_year, "end_year": start_year + 1, "church_year": church_year, "seasons": seasons, "months": months })

def about(request):
    return render(request, "office/about.html")

def now(request):
    return render(request, "office/evening_prayer/redirect.html", {})
