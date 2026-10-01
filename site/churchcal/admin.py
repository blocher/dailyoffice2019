import calendar

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from churchcal.models import Commemoration, SanctoraleCommemoration, SanctoraleBasedCommemoration
from standrew.bios import go_perplexity


class AIRegenerateAdminMixin:
    """Admin helpers to regenerate Perplexity-backed AI bio fields for a single feast."""

    actions = ("regenerate_ai_content",)

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                "<path:object_id>/regenerate-ai/",
                self.admin_site.admin_view(self.regenerate_ai_view),
                name="%s_%s_regenerate_ai" % info,
            ),
        ]
        return custom + super().get_urls()

    def regenerate_ai_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj is None:
            self.message_user(request, "Commemoration not found.", level=messages.ERROR)
            changelist = reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist")
            return redirect(request.META.get("HTTP_REFERER") or changelist)

        try:
            go_perplexity(obj, overwrite=True)
            self.message_user(
                request,
                f"Regenerated AI content for “{obj.name}”. Review the fields below.",
            )
        except Exception as e:
            self.message_user(
                request,
                f"Failed to regenerate AI content for “{obj.name}”: {e}",
                level=messages.ERROR,
            )

        return redirect(
            reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_change",
                args=[obj.pk],
            )
        )

    @admin.action(description="Regenerate AI content (Perplexity fields)")
    def regenerate_ai_content(self, request, queryset):
        succeeded = 0
        for obj in queryset:
            try:
                go_perplexity(obj, overwrite=True)
                succeeded += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to regenerate “{obj.name}”: {e}",
                    level=messages.ERROR,
                )
        if succeeded:
            self.message_user(
                request,
                f"Regenerated AI content for {succeeded} commemorations.",
            )

    @admin.display(description="AI actions")
    def regenerate_ai_button(self, obj):
        if not obj or not obj.pk:
            return "Save this feast first, then regenerate."
        url = reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_regenerate_ai",
            args=[obj.pk],
        )
        return format_html(
            '<a class="button" href="{}" '
            "onclick=\"return confirm('Overwrite existing AI fields for this feast? "
            "This calls Perplexity for each field and may take 1–2 minutes.')\">"
            "Regenerate AI content</a>",
            url,
        )


AI_GENERATION_FIELDSET = (
    "AI Generation",
    {
        "fields": (
            "ai_generation_instructions",
            "regenerate_ai_button",
        ),
        "description": (
            "Add feast-specific instructions (e.g. do not confuse this saint with another), "
            "save the form, then click Regenerate AI content. Only Perplexity-backed fields "
            "shown on the site are overwritten."
        ),
    },
)

AI_CONTENT_FIELDSET = (
    "AI Content",
    {
        "classes": ("collapse",),
        "fields": (
            "ai_one_sentence",
            "ai_quote",
            "ai_quote_by",
            "ai_quote_citations",
            "ai_verse",
            "ai_verse_citation",
            "ai_hagiography",
            "ai_hagiography_citations",
            "ai_legend_title",
            "ai_legend",
            "ai_legend_citations",
            "ai_bullet_points",
            "ai_bullet_points_citations",
            "ai_traditions",
            "ai_traditions_citations",
            "ai_foods",
            "ai_foods_citations",
            "ai_image_1",
            "ai_image_2",
        ),
    },
)


class CommemorationAdmin(AIRegenerateAdminMixin, admin.ModelAdmin):
    list_display = ("name", "date", "rank", "color", "calendar", "biography")
    search_fields = ("name",)
    list_filter = (
        "calendar",
        "rank",
        "color",
    )
    readonly_fields = ("regenerate_ai_button",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "rank",
                    "calendar",
                    "color",
                    "additional_color",
                    "alternate_color",
                    "alternate_color_2",
                    "color_notes",
                    "cannot_occur_after",
                    "collect_1",
                    "collect_2",
                    "collect_eve",
                    "link_1",
                    "link_2",
                    "link_3",
                    "biography",
                    "image_link",
                ),
            },
        ),
        AI_GENERATION_FIELDSET,
        AI_CONTENT_FIELDSET,
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("rank", "calendar__denomination")
        return queryset

    def date(self, obj):
        if hasattr(obj, "month"):
            return "{}-{} {} {}".format(obj.month, obj.day, calendar.month_name[obj.month], obj.day)


class SanctoraleCommemorationAdmin(AIRegenerateAdminMixin, admin.ModelAdmin):
    list_display = ("name", "month", "day", "saint_type", "rank", "color", "calendar")

    search_fields = ("name", "saint_name")
    list_filter = (
        "calendar",
        "saint_type",
        "rank",
        "color",
    )
    readonly_fields = ("regenerate_ai_button",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "month",
                    "day",
                    "saint_name",
                    "saint_type",
                    "saint_gender",
                    "saint_fill_in_the_blank",
                    "common",
                    "rank",
                    "calendar",
                    "color",
                    "additional_color",
                    "alternate_color",
                    "alternate_color_2",
                    "color_notes",
                    "cannot_occur_after",
                    "collect_1",
                    "collect_2",
                    "collect_eve",
                    "link_1",
                    "link_2",
                    "link_3",
                    "biography",
                    "image_link",
                ),
            },
        ),
        AI_GENERATION_FIELDSET,
        AI_CONTENT_FIELDSET,
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("rank", "calendar__denomination")
        return queryset

    def date(self, obj):
        if hasattr(obj, "month"):
            return "{}-{} {} {}".format(obj.month, obj.day, calendar.month_name[obj.month], obj.day)


class SanctoraleBasedCommemorationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "weekday",
        "number_after",
        "month_after",
        "day_after",
        "additional_days_after",
        "rank",
        "color",
        "calendar",
    )

    search_fields = ("name",)
    list_filter = (
        "calendar",
        "rank",
        "color",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("rank", "calendar__denomination")
        return queryset

    def date(self, obj):
        if hasattr(obj, "month"):
            return "{}-{} {} {}".format(obj.month, obj.day, calendar.month_name[obj.month], obj.day)


admin.site.register(Commemoration, CommemorationAdmin)
admin.site.register(SanctoraleCommemoration, SanctoraleCommemorationAdmin)
admin.site.register(SanctoraleBasedCommemoration, SanctoraleBasedCommemorationAdmin)
