from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone

from office.models import (
    AboutItem,
    AudioCostRate,
    AudioGeneratedFile,
    AudioGenerationConfig,
    AudioGenerationEvent,
    AudioUsage,
    AudioVoice,
    UpdateNotice,
    StandardOfficeDay,
    HolyDayOfficeDay,
    Setting,
    SettingOption,
    Collect,
    CollectTag,
    CollectTagCategory,
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


@admin.action(description="Disable selected audio files")
def disable_audio_files(modeladmin, request, queryset):
    for generated_file in queryset:
        generated_file.mark_disabled()


@admin.action(description="Mark selected audio files as deleted")
def mark_audio_files_deleted(modeladmin, request, queryset):
    for generated_file in queryset:
        generated_file.mark_deleted()


@admin.action(description="Run Studio access health check")
def run_studio_health_check(modeladmin, request, queryset):
    from office.audio.providers import get_audio_provider

    for config in queryset:
        previous_mode = config.provider_mode
        previous_studio_enabled = config.elevenlabs_studio_enabled
        config.provider_mode = AudioGenerationConfig.ProviderMode.ELEVENLABS_STUDIO
        config.elevenlabs_studio_enabled = True
        config.save(
            update_fields=[
                "provider_mode",
                "elevenlabs_studio_enabled",
                "updated",
            ]
        )
        get_audio_provider(config)
        config.provider_mode = previous_mode
        config.elevenlabs_studio_enabled = previous_studio_enabled
        config.save(update_fields=["provider_mode", "elevenlabs_studio_enabled", "updated"])


class AudioGenerationConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider_mode",
        "elevenlabs_model_id",
        "elevenlabs_sound_model_id",
        "elevenlabs_studio_enabled",
        "elevenlabs_studio_access_granted",
        "elevenlabs_studio_last_checked",
    )
    fieldsets = (
        (
            "Provider",
            {
                "fields": (
                    "name",
                    "provider_mode",
                    "openai_model",
                    "openai_output_format",
                )
            },
        ),
        (
            "ElevenLabs v3",
            {
                "fields": (
                    "elevenlabs_model_id",
                    "elevenlabs_sound_model_id",
                    "elevenlabs_output_format",
                    "elevenlabs_language_code",
                    "elevenlabs_apply_text_normalization",
                    "elevenlabs_seed",
                )
            },
        ),
        (
            "Studio",
            {
                "fields": (
                    "elevenlabs_studio_enabled",
                    "elevenlabs_studio_access_granted",
                    "elevenlabs_studio_last_checked",
                    "elevenlabs_studio_last_error",
                )
            },
        ),
        (
            "Sound and Assembly",
            {
                "fields": (
                    "sound_default_duration_seconds",
                    "sound_prompt_influence",
                    "sound_loop",
                    "spoken_chunk_target_characters",
                    "spoken_chunk_max_characters",
                    "assembly_target_loudness_lufs",
                    "sound_target_loudness_lufs",
                    "module_boundary_padding_ms",
                    "settings_notes",
                )
            },
        ),
    )
    readonly_fields = (
        "elevenlabs_studio_access_granted",
        "elevenlabs_studio_last_checked",
        "elevenlabs_studio_last_error",
    )
    actions = (run_studio_health_check,)


class AudioVoiceAdmin(admin.ModelAdmin):
    list_display = ("provider", "role", "name", "voice_id", "enabled", "order")
    list_editable = ("enabled", "order")
    list_filter = ("provider", "role", "enabled")
    search_fields = ("name", "voice_id")
    ordering = ("provider", "role", "order", "name")


class AudioGeneratedFileAdmin(admin.ModelAdmin):
    list_display = (
        "created",
        "provider_mode",
        "generation_type",
        "status",
        "module_name",
        "model_id",
        "duration_seconds",
        "characters",
        "cost_usd",
        "cost_source",
        "disabled_at",
        "deleted_at",
    )
    list_filter = (
        "provider",
        "provider_mode",
        "generation_type",
        "status",
        "office_date",
        "module_name",
        "model_id",
        "disabled_at",
        "deleted_at",
    )
    search_fields = (
        "cache_key",
        "content_hash",
        "text_preview",
        "module_name",
        "line_id",
        "settings_hash",
        "request_id",
        "file_name",
    )
    readonly_fields = (
        "cache_key",
        "content_hash",
        "settings_hash",
        "settings_snapshot",
        "response_metadata",
        "created",
        "updated",
    )
    actions = (disable_audio_files, mark_audio_files_deleted)
    date_hierarchy = "created"


class AudioGenerationEventAdmin(admin.ModelAdmin):
    change_list_template = "admin/office/audio_spend_changelist.html"
    list_display = (
        "created",
        "action",
        "provider_mode",
        "generation_type",
        "module_name",
        "model_id",
        "characters",
        "cost_units",
        "cost_usd",
        "request_id",
    )
    list_filter = ("action", "provider", "provider_mode", "generation_type", "office_date", "module_name", "model_id")
    search_fields = ("cache_key", "settings_hash", "request_id", "error_message", "metadata")
    date_hierarchy = "created"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            queryset = response.context_data["cl"].queryset
            response.context_data["audio_spend_totals"] = queryset.values("provider").annotate(
                cost_usd=Sum("cost_usd"),
                cost_units=Sum("cost_units"),
                characters=Sum("characters"),
            )
            response.context_data["audio_spend_generated_total"] = queryset.filter(
                action=AudioGenerationEvent.Action.GENERATED
            ).aggregate(cost_usd=Sum("cost_usd"))
            response.context_data["audio_spend_as_of"] = timezone.now()
        except (AttributeError, KeyError):
            pass
        return response


class AudioUsageAdmin(admin.ModelAdmin):
    list_display = (
        "created",
        "office_date",
        "office",
        "module_name",
        "line_type",
        "provider_mode",
        "generation_type",
        "settings_hash",
        "generated_file",
    )
    list_filter = ("office_date", "office", "module_name", "line_type", "provider_mode", "generation_type")
    search_fields = ("settings_hash", "settings_snapshot", "line_id", "module_name", "generated_file__cache_key")
    date_hierarchy = "created"


class AudioCostRateAdmin(admin.ModelAdmin):
    list_display = ("provider", "model_id", "generation_type", "unit", "usd_per_unit", "effective_at", "enabled")
    list_filter = ("provider", "model_id", "generation_type", "unit", "enabled")
    search_fields = ("provider", "model_id", "notes")
    date_hierarchy = "effective_at"


admin.site.register(AboutItem, AboutItemAdmin)
admin.site.register(UpdateNotice, UpdateNoticeAdmin)
admin.site.register(StandardOfficeDay, StandardOfficeDayAdmin)
admin.site.register(HolyDayOfficeDay, HolyDayOfficeDayAdmin)
admin.site.register(Setting, OfficeSettingAdmin)
admin.site.register(CollectTag, CollectTagAdmin)
admin.site.register(CollectTagCategory, CollectTagCategoryAdmin)
admin.site.register(Collect, CollectAdmin)
admin.site.register(AudioGenerationConfig, AudioGenerationConfigAdmin)
admin.site.register(AudioVoice, AudioVoiceAdmin)
admin.site.register(AudioGeneratedFile, AudioGeneratedFileAdmin)
admin.site.register(AudioGenerationEvent, AudioGenerationEventAdmin)
admin.site.register(AudioUsage, AudioUsageAdmin)
admin.site.register(AudioCostRate, AudioCostRateAdmin)
