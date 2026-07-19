from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

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


class PronunciationOverrideAdmin(admin.ModelAdmin):
    list_display = ("match", "replacement", "is_regex", "order", "enabled", "note")
    list_editable = ("replacement", "is_regex", "order", "enabled")
    list_filter = ("enabled", "is_regex")
    search_fields = ("match", "replacement", "note")
    ordering = ("order", "id")


class AudioClipAdmin(admin.ModelAdmin):
    list_display = ("text", "voice", "line_type", "kind", "duration", "model", "speed", "updated", "clip_actions")
    list_filter = ("voice", "line_type", "kind", "model")
    search_fields = ("text", "voice", "line_type", "key", "filename")
    readonly_fields = ("key", "filename", "duration", "created", "updated")
    ordering = ("line_type", "voice", "text")
    actions = ("delete_and_rebuild",)

    def get_urls(self):
        custom = [
            path(
                "<uuid:object_id>/regenerate/",
                self.admin_site.admin_view(self.regenerate_clip_view),
                name="office_audioclip_regenerate",
            ),
            path(
                "<uuid:object_id>/delete-clip/",
                self.admin_site.admin_view(self.delete_clip_view),
                name="office_audioclip_delete_clip",
            ),
        ]
        return custom + super().get_urls()

    @admin.display(description="Actions")
    def clip_actions(self, obj):
        return format_html(
            '<a class="button" href="{}" '
            "onclick=\"return confirm('Delete this clip and re-synthesize the exact same text?')\">"
            "Regenerate</a>&nbsp;"
            '<a class="button" style="background:#ba2121;color:#fff" href="{}" '
            "onclick=\"return confirm('Delete this clip and its audio file?')\">Delete</a>",
            reverse("admin:office_audioclip_regenerate", args=[obj.pk]),
            reverse("admin:office_audioclip_delete_clip", args=[obj.pk]),
        )

    def _back(self, request):
        return redirect(request.META.get("HTTP_REFERER") or "admin:office_audioclip_changelist")

    def regenerate_clip_view(self, request, object_id):
        clip = self.get_object(request, str(object_id))
        if clip is None:
            self.message_user(request, "Audio clip not found.", level=messages.ERROR)
            return self._back(request)

        import os

        from mutagen.mp3 import MP3

        from office.api.views.index import GenericDailyOfficeSerializer

        try:
            clip.delete_file()
            os.makedirs(os.path.dirname(clip.file_path), exist_ok=True)
            GenericDailyOfficeSerializer.synthesize_speech(clip.voice, clip.text, clip.file_path)
            try:
                clip.duration = MP3(clip.file_path).info.length
            except Exception:
                clip.duration = None
            clip.save()
            self.message_user(request, f"Regenerated audio for “{clip}”.")
        except Exception as e:
            self.message_user(request, f"Failed to regenerate “{clip}”: {e}", level=messages.ERROR)
        return self._back(request)

    def delete_clip_view(self, request, object_id):
        clip = self.get_object(request, str(object_id))
        if clip is None:
            self.message_user(request, "Audio clip not found.", level=messages.ERROR)
            return self._back(request)
        label = str(clip)
        had_file = clip.delete_file()
        clip.delete()
        suffix = " and its audio file" if had_file else " (no file on disk)"
        self.message_user(request, f"Deleted “{label}”{suffix}.")
        return self._back(request)

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
admin.site.register(SiteMessage, SiteMessageAdmin)
admin.site.register(StandardOfficeDay, StandardOfficeDayAdmin)
admin.site.register(HolyDayOfficeDay, HolyDayOfficeDayAdmin)
admin.site.register(Setting, OfficeSettingAdmin)
admin.site.register(CollectTag, CollectTagAdmin)
admin.site.register(CollectTagCategory, CollectTagCategoryAdmin)
admin.site.register(Collect, CollectAdmin)
