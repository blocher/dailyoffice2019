import json
from datetime import timedelta

from django.apps import apps
from django.contrib import admin
from django.db.models import Count, Q
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import TruncDate
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from analytics.models import AnalyticsEvent

OFFICE_LABELS = {
    "morning_prayer": "Morning Prayer",
    "midday_prayer": "Midday Prayer",
    "evening_prayer": "Evening Prayer",
    "early_evening_prayer": "Early Evening Prayer",
    "compline": "Compline",
    "close_of_day_prayer": "Close of Day",
}


def _views(event_type=AnalyticsEvent.OFFICE_VIEW):
    return Count("id", filter=Q(event_type=event_type))


def _unique_users(event_type=AnalyticsEvent.OFFICE_VIEW):
    return Count("client_id", distinct=True, filter=Q(event_type=event_type) & ~Q(client_id=""))


def _setting_definitions():
    """Ordered, de-duplicated list of ``{name, title}`` for known settings."""
    setting_model = apps.get_model("office", "Setting")
    seen = {}
    for row in setting_model.objects.order_by("site", "setting_type", "order").values("name", "title"):
        seen.setdefault(row["name"], row["title"] or row["name"])
    return [{"name": name, "title": title} for name, title in seen.items()]


def _option_labels(setting_name):
    """Map a setting's stored value -> human label (``SettingOption.name``)."""
    option_model = apps.get_model("office", "SettingOption")
    return dict(option_model.objects.filter(setting__name=setting_name).values_list("value", "name"))


def _value_distribution(office_qs, setting_name):
    """Count of each stored value for one setting, most common first."""
    return list(
        office_qs.annotate(val=KeyTextTransform(setting_name, "settings"))
        .exclude(val__isnull=True)
        .exclude(val="")
        .values("val")
        .annotate(count=Count("id"))
        .order_by("-count")
    )


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("created", "event_type", "service_type", "office", "platform", "browser", "os", "client_id")
    list_filter = ("event_type", "service_type", "office", "platform", "browser", "os")
    search_fields = ("client_id", "office", "browser", "os")
    date_hierarchy = "created"
    ordering = ("-created",)
    readonly_fields = tuple(f.name for f in AnalyticsEvent._meta.fields)
    change_list_template = "admin/analytics/analyticsevent/change_list.html"

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "dashboard/",
                self.admin_site.admin_view(self.dashboard_view),
                name="analytics_dashboard",
            ),
        ]
        return custom + urls

    def dashboard_view(self, request):
        try:
            days = max(1, min(int(request.GET.get("days", 30)), 365))
        except (TypeError, ValueError):
            days = 30
        since = timezone.now() - timedelta(days=days)
        qs = AnalyticsEvent.objects.filter(created__gte=since)

        per_office = list(
            qs.values("service_type", "office")
            .annotate(
                views=_views(),
                audio_play=_views(AnalyticsEvent.AUDIO_PLAY),
                unique_users=_unique_users(),
            )
            .order_by("service_type", "office")
        )
        for row in per_office:
            row["office_label"] = OFFICE_LABELS.get(row["office"], row["office"] or "—")
            row["play_rate"] = round(100 * row["audio_play"] / row["views"], 1) if row["views"] else 0

        def breakdown(field):
            rows = list(
                qs.filter(event_type=AnalyticsEvent.OFFICE_VIEW)
                .values(field)
                .annotate(views=Count("id"), unique_users=_unique_users())
                .order_by("-views")
            )
            for row in rows:
                row["label"] = row[field] or "Unknown"
            return rows

        totals = qs.aggregate(
            views=_views(),
            audio_play=_views(AnalyticsEvent.AUDIO_PLAY),
            audio_loaded=_views(AnalyticsEvent.AUDIO_LOADED),
            unique_users=_unique_users(),
        )

        daily = list(
            qs.annotate(day=TruncDate("created"))
            .values("day")
            .annotate(
                views=_views(),
                audio_play=_views(AnalyticsEvent.AUDIO_PLAY),
                audio_loaded=_views(AnalyticsEvent.AUDIO_LOADED),
            )
            .order_by("day")
        )
        chart_data = {
            "labels": [row["day"].isoformat() for row in daily],
            "views": [row["views"] for row in daily],
            "audio_play": [row["audio_play"] for row in daily],
            "audio_loaded": [row["audio_loaded"] for row in daily],
        }

        # --- Settings usage ------------------------------------------------
        office_qs = qs.filter(event_type=AnalyticsEvent.OFFICE_VIEW)
        setting_defs = _setting_definitions()
        setting_names = [d["name"] for d in setting_defs]

        selected_setting = request.GET.get("setting")
        if selected_setting not in setting_names:
            selected_setting = setting_names[0] if setting_names else None

        setting_distribution = []
        setting_chart = {"labels": [], "counts": []}
        selected_title = selected_setting
        if selected_setting:
            selected_title = next(
                (d["title"] for d in setting_defs if d["name"] == selected_setting), selected_setting
            )
            labels = _option_labels(selected_setting)
            rows = _value_distribution(office_qs, selected_setting)
            total = sum(row["count"] for row in rows) or 1
            for row in rows:
                row["label"] = labels.get(row["val"], row["val"])
                row["share"] = round(100 * row["count"] / total, 1)
            setting_distribution = rows
            setting_chart = {
                "labels": [row["label"] for row in rows],
                "counts": [row["count"] for row in rows],
            }

        # Overview: most common value per setting.
        settings_overview = []
        for definition in setting_defs:
            rows = _value_distribution(office_qs, definition["name"])
            if not rows:
                continue
            total = sum(row["count"] for row in rows)
            top = rows[0]
            labels = _option_labels(definition["name"])
            settings_overview.append(
                {
                    "name": definition["name"],
                    "title": definition["title"],
                    "top_label": labels.get(top["val"], top["val"]),
                    "top_count": top["count"],
                    "top_share": round(100 * top["count"] / total, 1) if total else 0,
                    "distinct_values": len(rows),
                }
            )

        context = {
            **self.admin_site.each_context(request),
            "title": "Analytics dashboard",
            "days": days,
            "day_options": (7, 30, 90, 365),
            "per_office": per_office,
            "platform_rows": breakdown("platform"),
            "os_rows": breakdown("os"),
            "browser_rows": breakdown("browser"),
            "totals": totals,
            "chart_data_json": json.dumps(chart_data),
            "setting_defs": setting_defs,
            "selected_setting": selected_setting,
            "selected_setting_title": selected_title,
            "setting_distribution": setting_distribution,
            "setting_chart_json": json.dumps(setting_chart),
            "settings_overview": settings_overview,
        }
        return TemplateResponse(request, "admin/analytics/dashboard.html", context)
