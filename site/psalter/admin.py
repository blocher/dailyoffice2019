from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from psalter.models import PsalmTopic


class PsalmTopicAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("topic_name", "psalms")
    fields = ("topic_name", "psalms")


admin.site.register(PsalmTopic, PsalmTopicAdmin)
