from django.contrib import admin
from .models import Sermon


class SermonAdmin(admin.ModelAdmin):
    list_display = ("title",)


admin.site.register(Sermon, SermonAdmin)
