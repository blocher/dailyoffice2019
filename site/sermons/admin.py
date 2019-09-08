from array_tags import widgets
from django import forms
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.shortcuts import render, redirect
from django.urls import path, reverse

from .models import Sermon, SermonDateTime, SermonBiblePassage, SermonLocation


class ImportForm(forms.Form):
    file = forms.FileField()


class SermonDateTimeInline(admin.TabularInline):
    model = SermonDateTime
    extra = 0


class SermonBiblePassageInline(admin.TabularInline):
    model = SermonBiblePassage
    extra = 0
    ordering = ["type"]


class SermonAdmin(admin.ModelAdmin):
    list_display = ("title",)
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

    inlines = (SermonDateTimeInline, SermonBiblePassageInline)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path("import-sermon/", self.import_sermon)]
        return new_urls + urls

    def import_sermon(self, request):
        if request.method == "POST":
            file = request.FILES["file"]
            sermon = Sermon.objects.create()
            sermon.file = file
            sermon.title = sermon.getTitle(file)
            sermon.content = sermon.getContent(file)
            sermon.text = sermon.getText(file)
            sermon.auto_summary = sermon.getSummary()

            sermon.getKeyWords()
            sermon.getBiblePassages(file)

            import datefinder

            matches = list(datefinder.find_dates(sermon.text))
            if len(matches) > 0:
                if matches[0].hour == 0:
                    matches[0] = matches[0].replace(hour=10, minute=0, second=0, microsecond=0)
                sermon.primary_date_and_time_given = matches[0]

            sermon.save()

            if sermon.primary_date_and_time_given:
                SermonDateTime.objects.create(
                    sermon_id=sermon.pk, date_and_time_given=sermon.primary_date_and_time_given, primary=True
                )

            self.message_user(request, "Your file has been imported")
            return redirect(reverse("admin:sermons_sermon_change", args=(sermon.pk,)))
        form = ImportForm()
        payload = {"form": form}
        return render(request, "admin/import_sermon.html", payload)


class SermonLocationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    fields = ("name", "address", "website", "alternate_names")

    formfield_overrides = {ArrayField: {"widget": widgets.AdminTagWidget}}


admin.site.register(SermonLocation, SermonLocationAdmin)
admin.site.register(Sermon, SermonAdmin)
