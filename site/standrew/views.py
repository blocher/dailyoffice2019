from datetime import datetime

from django.http import HttpResponse
from django.template.loader import render_to_string
from standrew.email import weekly_email


def current_email(request):
    modules = [module.render() for module in weekly_email()]
    context = {"modules": modules }


    html = render_to_string("emails/weekly_email.html", context)
    return HttpResponse(html)
