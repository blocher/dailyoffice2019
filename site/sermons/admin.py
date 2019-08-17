from django.contrib import admin
from django import forms
from django.urls import path, reverse
from .models import Sermon, SermonDateTime
from django.shortcuts import render, redirect


class ImportForm(forms.Form):
    file = forms.FileField()


class SermonDateTimeInline(admin.TabularInline):
    model = SermonDateTime
    extra = 0


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

    inlines = (SermonDateTimeInline,)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path("import-sermon/", self.import_sermon)]
        return new_urls + urls

    def import_sermon(self, request):
        if request.method == "POST":
            file = request.FILES["file"]
            sermon = Sermon.objects.create()
            sermon.title = "Poo ninnymuggins 2"
            sermon.file = file
            sermon.content = sermon.getContent(file)
            sermon.text = sermon.getText(file)
            sermon.auto_summary = sermon.getSummary()
            sermon.getKeyWords()

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


admin.site.register(Sermon, SermonAdmin)
