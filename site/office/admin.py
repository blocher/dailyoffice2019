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
    AudioClip,
    PronunciationOverride,
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


class PronunciationOverrideAdmin(admin.ModelAdmin):
    list_display = ("match", "replacement", "is_regex", "order", "enabled", "note")
    list_editable = ("replacement", "is_regex", "order", "enabled")
    list_filter = ("enabled", "is_regex")
    search_fields = ("match", "replacement", "note")
    ordering = ("order", "id")


class AudioClipAdmin(admin.ModelAdmin):
    list_display = ("text", "voice", "line_type", "kind", "duration", "model", "speed", "updated")
    list_filter = ("voice", "line_type", "kind", "model")
    search_fields = ("text", "voice", "line_type", "key", "filename")
    readonly_fields = ("key", "filename", "duration", "created", "updated")
    ordering = ("line_type", "voice", "text")
    actions = ("delete_and_rebuild",)

    @admin.action(description="Delete file(s) and rebuild on next request")
    def delete_and_rebuild(self, request, queryset):
        deleted_files = 0
        for clip in queryset:
            if clip.delete_file():
                deleted_files += 1
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f"Removed {count} clip record(s) and {deleted_files} file(s). "
            f"They will regenerate the next time the audio is requested.",
        )


admin.site.register(PronunciationOverride, PronunciationOverrideAdmin)
admin.site.register(AudioClip, AudioClipAdmin)
admin.site.register(AboutItem, AboutItemAdmin)
admin.site.register(UpdateNotice, UpdateNoticeAdmin)
admin.site.register(StandardOfficeDay, StandardOfficeDayAdmin)
admin.site.register(HolyDayOfficeDay, HolyDayOfficeDayAdmin)
admin.site.register(Setting, OfficeSettingAdmin)
admin.site.register(CollectTag, CollectTagAdmin)
admin.site.register(CollectTagCategory, CollectTagCategoryAdmin)
admin.site.register(Collect, CollectAdmin)
