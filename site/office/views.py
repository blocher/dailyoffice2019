from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from office.offices import EveningPrayer


def today_evening_prayer(request):
    ep = EveningPrayer(timezone.now())
    return render(request, "office/evening_prayer/ep.html", {"ep": ep})
