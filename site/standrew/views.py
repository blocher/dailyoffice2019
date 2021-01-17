from datetime import datetime

from django.http import HttpResponse
from django.template.loader import render_to_string
from standrew.email import weekly_email, CommemorationDailyEmailModule


def current_email(request):
    modules = [module for module in weekly_email()]
    content = [module.render() for module in modules]
    context = {"modules": content, "heading": "The Week Ahead"}

    html = render_to_string("emails/weekly_email.html", context)
    return HttpResponse(html)


def feast_email(request):
    modules = [CommemorationDailyEmailModule()]
    content = [module.render() for module in modules]
    context = {"modules": content}

    html = render_to_string("emails/weekly_email.html", context)
    return HttpResponse(html)
