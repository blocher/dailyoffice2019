from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from office.models import (
    AboutItem,
    UpdateNotice,
    StandardOfficeDay,
    HolyDayOfficeDay,
    Setting,
    SettingOption,
    CollectCategory,
    Collect,
)


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


class HolyDayOfficeDayAdmin(admin.ModelAdmin):
    list_display = ("holy_day_name", "mp_psalms", "ep_psalms", "order")
    ordering = ("order",)


class OfficeSettingOptionInlineAdmin(admin.TabularInline):
    model = SettingOption
    ordering = ("order",)
    extra = 0


class OfficeSettingAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "get_site_display",
        "get_setting_type_display",
        "order",
    )
    ordering = ("site", "setting_type", "order")
    extra = 0
    inlines = (OfficeSettingOptionInlineAdmin,)
    list_filter = ("site", "setting_type")

    def get_site_display(self, obj):
        return obj.get_site_display()

    get_site_display.short_description = "Site"

    def get_setting_type_display(self, obj):
        return obj.get_setting_type_display()

    get_setting_type_display.short_description = "Setting Type"


class CollectCategoryAdmin(admin.ModelAdmin):
    model = CollectCategory
    ordering = ("order",)
    extra = 0

    list_display = ("name", "order")


class CollectAdmin(admin.ModelAdmin):
    model = Collect
    ordering = ("order",)
    extra = 0

    list_display = ("title", "order", "collect_type", "collect_category", "attribution")


admin.site.register(AboutItem, AboutItemAdmin)
admin.site.register(UpdateNotice, UpdateNoticeAdmin)
admin.site.register(StandardOfficeDay, StandardOfficeDayAdmin)
admin.site.register(HolyDayOfficeDay, HolyDayOfficeDayAdmin)
admin.site.register(Setting, OfficeSettingAdmin)
admin.site.register(CollectCategory, CollectCategoryAdmin)
admin.site.register(Collect, CollectAdmin)
