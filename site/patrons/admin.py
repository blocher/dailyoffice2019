from django.contrib import admin, messages
from django.utils.html import format_html

from patrons.models import (
    CalendarFeed,
    Event,
    FamilyMember,
    PatronalFeast,
    TextMessageSend,
    TextRecipient,
    TextSchedule,
)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "first_name", "middle_name", "confirmation_name", "maiden_name", "last_name")
    search_fields = ("first_name", "middle_name", "confirmation_name", "maiden_name", "last_name")
    list_filter = ("last_name",)


@admin.register(TextRecipient)
class TextRecipientAdmin(admin.ModelAdmin):
    list_display = ("family_member", "telephone_number", "enabled", "updated")
    list_filter = ("enabled",)
    search_fields = ("family_member__first_name", "family_member__last_name", "telephone_number")
    autocomplete_fields = ("family_member",)
    list_editable = ("enabled",)


@admin.register(TextSchedule)
class TextScheduleAdmin(admin.ModelAdmin):
    list_display = ("time", "relative_days", "updated")
    list_filter = ("relative_days",)


@admin.register(PatronalFeast)
class PatronalFeastAdmin(admin.ModelAdmin):
    list_display = ("family_member", "normalized_name", "display_feast_name", "date_summary")
    list_filter = ("family_member",)
    search_fields = (
        "family_member__first_name",
        "family_member__last_name",
        "normalized_name",
        "feast_name",
        "general_calendar_name",
        "traditional_calendar_name",
        "episcopal_calendar_name",
    )
    autocomplete_fields = ("family_member",)
    fieldsets = (
        (None, {"fields": ("family_member", "normalized_name", "feast_name")}),
        (
            "Calendar Names",
            {"fields": ("general_calendar_name", "traditional_calendar_name", "episcopal_calendar_name")},
        ),
        (
            "Calendar Dates",
            {
                "fields": (
                    ("general_month", "general_day"),
                    ("traditional_month", "traditional_day"),
                    ("episcopal_month", "episcopal_day"),
                )
            },
        ),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("family_member", "event_type", "date", "details")
    list_filter = ("event_type", "date")
    search_fields = ("family_member__first_name", "family_member__last_name", "details")
    autocomplete_fields = ("family_member",)
    date_hierarchy = "date"


@admin.register(TextMessageSend)
class TextMessageSendAdmin(admin.ModelAdmin):
    list_display = (
        "attempted_at",
        "recipient",
        "target",
        "occurrence_date",
        "schedule",
        "success",
        "provider_message_id",
    )
    list_filter = ("success", "occurrence_date", "attempted_at")
    search_fields = (
        "recipient__family_member__first_name",
        "recipient__family_member__last_name",
        "recipient__telephone_number",
        "message",
        "provider_message_id",
        "error_message",
    )
    autocomplete_fields = ("recipient", "event", "patronal_feast")
    readonly_fields = ("attempted_at", "updated")
    date_hierarchy = "attempted_at"

    def target(self, obj):
        return obj.event or obj.patronal_feast


@admin.register(CalendarFeed)
class CalendarFeedAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled", "calendar_url", "updated")
    readonly_fields = ("token", "subscription_link", "created", "updated")
    actions = ("rotate_tokens",)

    def calendar_url(self, obj):
        return obj.subscription_url

    def subscription_link(self, obj):
        if not obj.pk:
            return "Save this feed to generate a subscription URL."
        return format_html('<a href="{}">{}</a>', obj.subscription_url, obj.subscription_url)

    @admin.action(description="Rotate selected calendar tokens")
    def rotate_tokens(self, request, queryset):
        count = 0
        for feed in queryset:
            feed.rotate_token()
            count += 1
        self.message_user(request, "Rotated {} calendar token(s).".format(count), messages.SUCCESS)
