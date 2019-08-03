from django.http import HttpResponse

from django.shortcuts import render

from .models import Sermon


def sermons(request):
    sermons = Sermon.objects.all()
    return render(request, "../templates/sermons.html", {"sermons": sermons})


def sermon(request, id):
    sermon = Sermon.objects.filter(pk=id).first()
    return render(request, "../templates/sermon.html", {"sermon": sermon})
