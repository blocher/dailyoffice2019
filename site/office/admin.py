from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from office.models import (
    AboutItem,
    UpdateNotice,
    StandardOfficeDay,
    HolyDayOfficeDay,
    Setting,
    SettingOption,
    Collect,
    CollectTag,
    CollectTagCategory,
    SiteMessage,
)


class AboutItemAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("display_name", "app_mode", "web_mode")
    fields = ("question", "answer", "app_mode", "web_mode")
    list_filter = ("app_mode", "web_mode")


class UpdateNoticeAdmin(admin.ModelAdmin):
    list_display = ("version", "app_mode", "web_mode")
    fields = ("version", "notice", "app_mode", "web_mode")
    list_filter = ("app_mode", "web_mode")


class SiteMessageAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "tag_text",
        "tag_color",
        "active",
        "show_on_web",
        "show_on_android",
        "show_on_ios",
        "expiration_date",
        "order",
    )
    list_filter = ("active", "tag_color", "show_on_web", "show_on_android", "show_on_ios")
    search_fields = ("text", "tag_text", "link")
    list_editable = ("active", "order")
    fieldsets = (
        ("Content", {"fields": ("tag_text", "tag_color", "text", "link")}),
        ("Dismissal", {"fields": ("dismissible", "dismiss_permanent")}),
        ("Platforms", {"fields": ("show_on_web", "show_on_android", "show_on_ios")}),
        ("Visibility", {"fields": ("active", "expiration_date", "order")}),
    )


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


class CollectTagCategoryAdmin(admin.ModelAdmin):
    model = CollectTagCategory
    ordering = ("order",)
    extra = 0

    list_display = ("name", "order")


class CollectTagAdmin(admin.ModelAdmin):
    model = CollectTag
    ordering = ("name",)
    extra = 0

    list_display = ("name", "collect_tag_category")


class CollectAdmin(admin.ModelAdmin):
    model = Collect
    ordering = ("order",)
    extra = 0

    list_display = ("title", "order", "collect_type", "attribution", "created", "updated")
    list_filter = ("collect_type", "tags")
    search_fields = ("title", "attribution", "text", "traditional_text")


admin.site.register(AboutItem, AboutItemAdmin)
admin.site.register(UpdateNotice, UpdateNoticeAdmin)
admin.site.register(SiteMessage, SiteMessageAdmin)
admin.site.register(StandardOfficeDay, StandardOfficeDayAdmin)
admin.site.register(HolyDayOfficeDay, HolyDayOfficeDayAdmin)
admin.site.register(Setting, OfficeSettingAdmin)
admin.site.register(CollectTag, CollectTagAdmin)
admin.site.register(CollectTagCategory, CollectTagCategoryAdmin)
admin.site.register(Collect, CollectAdmin)
