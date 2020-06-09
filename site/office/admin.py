from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from office.models import AboutItem, UpdateNotice, StandardOfficeDay


class AboutItemAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("display_name", "app_mode", "web_mode")
    fields = ("question", "answer", "app_mode", "web_mode")
    list_filter = ("app_mode", "web_mode")

class UpdateNoticeAdmin(admin.ModelAdmin):
    list_display = ("version", "app_mode", "web_mode")
    fields = ("version", "notice", "app_mode", "web_mode")
    list_filter = ("app_mode", "web_mode")

class StandardOfficeDayAdmin(admin.ModelAdmin):
    list_display = ("month", "day", "mp_psalms", "ep_psalms")
    ordering = ("month", "day")



admin.site.register(AboutItem, AboutItemAdmin)
admin.site.register(UpdateNotice, UpdateNoticeAdmin)
admin.site.register(StandardOfficeDay, StandardOfficeDayAdmin)
