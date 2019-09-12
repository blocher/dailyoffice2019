from array_tags import widgets
from django import forms
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.shortcuts import render, redirect
from django.urls import path, reverse

from sermons.text_extractor import TextExtractor, WordXExtractor

from sermons.importer import SermonImporter
from sermons.text_extractor import TextExtractorFactory
from .models import Sermon, SermonDateTime, SermonBiblePassage, SermonLocation
from material.admin.decorators import register
from material.admin.options import MaterialModelAdmin


class ImportForm(forms.Form):
    file = forms.FileField()


class SermonDateTimeInline(admin.TabularInline):
    model = SermonDateTime
    extra = 0


class SermonBiblePassageInline(admin.TabularInline):
    model = SermonBiblePassage
    extra = 0
    ordering = ["type"]


@register(Sermon)
class SermonAdmin(MaterialModelAdmin):
    list_display = ("title", "primary_date_and_time_given", "location")
    fields = (
        "title",
        "location",
        "primary_date_and_time_given",
        "file",
        "summary",
        "auto_summary",
        "content",
        "notes",
        "private_notes",
    )
    readonly_fields = ("auto_summary", "primary_date_and_time_given")

    change_list_template = "admin/sermons_changelist.html"

    list_filter = ("location", "primary_date_and_time_given")
    inlines = (SermonDateTimeInline, SermonBiblePassageInline)

    ordering = ("-primary_date_and_time_given",)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path("import-sermon/", self.import_sermon)]
        return new_urls + urls

    def import_sermon(self, request):
        if request.method == "POST":
            file = request.FILES["file"]
            sermon = SermonImporter.import_file(file)
            return redirect("/admin/sermons/sermon/import-sermon/")
            self.message_user(request, "Your file has been imported")
            return redirect(reverse("admin:sermons_sermon_change", args=(sermon.pk,)))
        form = ImportForm()
        payload = {"form": form}
        return render(request, "admin/import_sermon.html", payload)


@register(SermonLocation)
class SermonLocationAdmin(MaterialModelAdmin):
    list_display = ("name",)
    fields = ("name", "address", "website", "alternate_names")

    formfield_overrides = {ArrayField: {"widget": widgets.AdminTagWidget}}


admin.site.register(SermonLocation, SermonLocationAdmin)
admin.site.register(Sermon, SermonAdmin)
