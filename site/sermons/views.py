from django.http import HttpResponse

from django.shortcuts import render, render_to_response

from .models import Sermon


def sermons(request):
    sermons = Sermon.objects.all()
    return render(request, "../templates/sermons.html", {"sermons": sermons})


def sermon(request, id):
    sermon = Sermon.objects.filter(pk=id).first()
    return render(request, "../templates/sermon.html", {"sermon": sermon})


def handle404(request, exception):
    response = render_to_response("404.html")
    response.status_code = 404
    return response
