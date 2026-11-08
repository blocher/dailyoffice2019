from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from psalter.chant import ai
from psalter.chant.notation import NotationError, validate
from psalter.chant.pointing import point_verse, segments
from psalter.chant.service import point_psalm, verse_texts
from psalter.chant.tones import get_tone
from psalter.models import Psalm, PsalmTopic, PsalmVerse, PsalmVersePointing

# Admin actions call the AI synchronously, so keep each request small.
MAX_PSALMS_PER_ACTION = 5

CHANT_PREVIEW_CSS = """
<style>
.chant-preview { font-family: Georgia, serif; font-size: 15px; line-height: 1.7; max-width: 52em; }
.chant-preview p { margin: 0 0 .1em; }
.chant-preview .second { padding-left: 2em; margin-bottom: .6em; }
.chant-preview .accent { text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 3px; font-weight: bold; }
.chant-preview .preparatory, .chant-preview .intonation { font-style: italic; text-decoration: underline dotted; text-underline-offset: 3px; }
.chant-preview .bar { color: #a33; padding: 0 .15em; font-weight: bold; }
.chant-preview .status { font: 11px sans-serif; padding: 1px 5px; border-radius: 3px; margin-left: .5em; color: #fff; }
.chant-preview .status-agreed, .chant-preview .status-approved { background: #2e7d32; }
.chant-preview .status-check, .chant-preview .status-dictionary { background: #b7791f; }
.chant-preview .status-needs_review { background: #c53030; }
.chant-preview .warning { font: 12px sans-serif; color: #c53030; margin: 0 0 .6em 2em; }
.chant-preview .legend { font: 12px sans-serif; color: #555; margin-bottom: 1em; }
</style>
"""

CHANT_LEGEND = (
    "<p class='legend'><span class='bar'>|</span> inflection begins &nbsp; "
    "<span class='accent'>accent</span> accented note &nbsp; "
    "<span class='preparatory'>preparatory</span> preparatory or intonation note</p>"
)


def segments_html(items):
    parts = []
    for item in items:
        if item["r"] == "bar":
            parts.append(mark_safe("<span class='bar'>|</span>"))
        elif item["r"] in ("accent", "preparatory", "intonation"):
            parts.append(format_html("<span class='{}'>{}</span>", item["r"], item["t"]))
        else:
            parts.append(format_html("{}", item["t"]))
    return format_html_join("", "{}", ((p,) for p in parts))


def pointed_verse_html(number, first_notation, second_notation, tone, status=None, link=None):
    try:
        first, second = point_verse(first_notation, second_notation, tone, first_verse=number == 1)
    except NotationError as error:
        return format_html("<p class='warning'>{}: {}</p>", number, error)
    badge = format_html("<span class='status status-{}'>{}</span>", status, status.replace("_", " ")) if status else ""
    if link:
        badge = format_html("<a href='{}'>{}</a>", link, badge or "edit")
    warnings = first.warnings + second.warnings
    return format_html(
        "<p><sup>{}</sup> {} *{}</p><p class='second'>{}</p>{}",
        number,
        segments_html(segments(first)),
        badge,
        segments_html(segments(second)),
        format_html("<p class='warning'>{}</p>", " ".join(warnings)) if warnings else "",
    )


class PsalmTopicAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("topic_name", "psalms")
    fields = ("topic_name", "psalms")


class VersesWithLord(SimpleListFilter):
    title = "Verses with Lord"
    parameter_name = "with_lord"

    def lookups(self, request, model_admin):
        return [
            (1, "Yes"),
            (0, "No"),
        ]

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except (TypeError, ValueError):
            return queryset
        if value == 1:
            return queryset.filter(
                Q(first_half__icontains="Lord")
                | Q(second_half__icontains="Lord")
                | Q(first_half_tle__icontains="Lord")
                | Q(second_half_tle__icontains="Lord")
            )
        if value == 0:
            return queryset.exclude(
                Q(first_half__icontains="Lord")
                | Q(second_half__icontains="Lord")
                | Q(first_half_tle__icontains="Lord")
                | Q(second_half_tle__icontains="Lord")
            )


class PsalmVerseAdmin(admin.ModelAdmin):
    list_display = ("psalm_number", "number", "first_half", "second_half", "first_half_tle", "second_half_tle")
    fields = ("psalm_number", "number", "first_half", "second_half", "first_half_tle", "second_half_tle", "psalm")
    readonly_fields = ("psalm_number",)
    list_filter = (VersesWithLord,)

    def psalm_number(self, obj):
        return obj.psalm.number

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("psalm").order_by("psalm__number", "number")
        return qs

    def psalm_number(self, obj):
        return obj.psalm.number


class PsalmAdmin(admin.ModelAdmin):
    list_display = ("number", "latin_title", "chant_tone", "pointed_verses", "verses_to_review")
    list_editable = ("chant_tone",)
    fields = ("number", "latin_title", "chant_tone", "chant_preview")
    readonly_fields = ("number", "latin_title", "chant_preview")
    search_fields = ("=number", "latin_title")
    ordering = ("number",)
    actions = ("point_with_ai", "point_with_dictionary")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _verses=Count("psalmverse", distinct=True),
                _pointed=Count("psalmverse__pointing", distinct=True),
                _to_review=Count(
                    "psalmverse__pointing",
                    filter=Q(
                        psalmverse__pointing__status__in=[PsalmVersePointing.NEEDS_REVIEW, PsalmVersePointing.CHECK]
                    ),
                    distinct=True,
                ),
            )
        )

    @admin.display(description="Pointed", ordering="_pointed")
    def pointed_verses(self, obj):
        return f"{obj._pointed} / {obj._verses}"

    @admin.display(description="To review", ordering="_to_review")
    def verses_to_review(self, obj):
        if not obj._to_review:
            return "—"
        url = reverse("admin:psalter_psalmversepointing_changelist")
        return format_html("<a href='{}?q={}&o=2'>{}</a>", url, obj.number, obj._to_review)

    @admin.display(description="Pointed for chant")
    def chant_preview(self, obj):
        tone = get_tone(obj.chant_tone)
        verses = PsalmVerse.objects.filter(psalm=obj).select_related("pointing").order_by("number")
        rows = []
        for verse in verses:
            pointing = getattr(verse, "pointing", None)
            if pointing is None:
                first_text, second_text = verse_texts(verse)
                rows.append(
                    format_html(
                        "<p><sup>{}</sup> {} *</p><p class='second'>{}</p>", verse.number, first_text, second_text
                    )
                )
                continue
            link = reverse("admin:psalter_psalmversepointing_change", args=[pointing.pk])
            rows.append(
                pointed_verse_html(
                    verse.number,
                    pointing.first_half_stress,
                    pointing.second_half_stress,
                    tone,
                    status=pointing.status,
                    link=link,
                )
            )
        if not any(hasattr(v, "pointing") for v in verses):
            note = format_html(
                "<p class='legend'>Not pointed yet. Use the “Point with AI” action on the psalm list, or run "
                "<code>manage.py point_psalms {}</code>.</p>",
                obj.number,
            )
        else:
            note = mark_safe(CHANT_LEGEND)
        return format_html(
            "{}<div class='chant-preview'><p class='legend'>{}</p>{}{}</div>",
            mark_safe(CHANT_PREVIEW_CSS),
            tone.label,
            note,
            format_html_join("", "{}", ((row,) for row in rows)),
        )

    def _point(self, request, queryset, use_ai):
        if queryset.count() > MAX_PSALMS_PER_ACTION:
            self.message_user(
                request,
                f"Choose at most {MAX_PSALMS_PER_ACTION} psalms at a time, or use manage.py point_psalms.",
                messages.ERROR,
            )
            return
        for psalm in queryset.order_by("number"):
            try:
                results = point_psalm(psalm, runs=2, use_ai=use_ai)
            except ai.StressMarkingError as error:
                self.message_user(request, f"Psalm {psalm.number}: {error}", messages.ERROR)
                return
            flagged = sum(
                1 for r in results if r.status in (PsalmVersePointing.NEEDS_REVIEW, PsalmVersePointing.CHECK)
            )
            self.message_user(request, f"Psalm {psalm.number}: pointed {len(results)} verses, {flagged} to review.")

    @admin.action(description="Point with AI (approved verses are kept)")
    def point_with_ai(self, request, queryset):
        self._point(request, queryset, use_ai=True)

    @admin.action(description="Point with the dictionary only (no AI)")
    def point_with_dictionary(self, request, queryset):
        self._point(request, queryset, use_ai=False)


class PsalmVersePointingForm(forms.ModelForm):
    class Meta:
        model = PsalmVersePointing
        fields = ("first_half_stress", "second_half_stress", "status")
        widgets = {
            "first_half_stress": forms.Textarea(attrs={"rows": 2, "cols": 100}),
            "second_half_stress": forms.Textarea(attrs={"rows": 2, "cols": 100}),
        }

    def clean(self):
        cleaned = super().clean()
        first_text, second_text = verse_texts(self.instance.verse)
        for field, text in (("first_half_stress", first_text), ("second_half_stress", second_text)):
            value = cleaned.get(field)
            if value is None:
                continue
            try:
                validate(value, text)
            except NotationError as error:
                self.add_error(field, str(error))
        return cleaned


class PsalmVersePointingAdmin(admin.ModelAdmin):
    form = PsalmVersePointingForm
    list_display = ("verse_label", "status", "confidence", "pointed")
    list_filter = ("status",)
    search_fields = ("=verse__psalm__number",)
    list_select_related = ("verse", "verse__psalm")
    list_per_page = 50
    readonly_fields = (
        "verse_label",
        "preview",
        "review_notes",
        "confidence",
        "ai_model",
        "ai_answers",
        "dictionary_first_half",
        "dictionary_second_half",
        "updated",
    )
    fieldsets = (
        (None, {"fields": ("verse_label", "preview", "status")}),
        (
            "Syllables and stresses",
            {
                "fields": ("first_half_stress", "second_half_stress"),
                "description": "Put / between syllables and + before each stressed syllable. Removing the marks must "
                "give back the verse text. Saving a change marks the verse approved.",
            },
        ),
        (
            "How it was pointed",
            {
                "fields": (
                    "review_notes",
                    "confidence",
                    "ai_model",
                    "ai_answers",
                    "dictionary_first_half",
                    "dictionary_second_half",
                    "updated",
                )
            },
        ),
    )
    actions = ("approve", "mark_needs_review")

    def has_add_permission(self, request):
        return False

    @admin.display(description="Verse", ordering="verse__psalm__number")
    def verse_label(self, obj):
        return f"Psalm {obj.verse.psalm.number}:{obj.verse.number}"

    @admin.display(description="Pointed")
    def pointed(self, obj):
        return format_html(
            "{}<div class='chant-preview'>{}</div>",
            mark_safe(CHANT_PREVIEW_CSS),
            pointed_verse_html(
                obj.verse.number, obj.first_half_stress, obj.second_half_stress, get_tone(obj.verse.psalm.chant_tone)
            ),
        )

    @admin.display(description="Preview")
    def preview(self, obj):
        tone = get_tone(obj.verse.psalm.chant_tone)
        psalm_url = reverse("admin:psalter_psalm_change", args=[obj.verse.psalm.pk])
        return format_html(
            "{}<div class='chant-preview'><p class='legend'>{} · <a href='{}'>whole psalm</a></p>{}{}</div>",
            mark_safe(CHANT_PREVIEW_CSS),
            tone.label,
            psalm_url,
            mark_safe(CHANT_LEGEND),
            pointed_verse_html(obj.verse.number, obj.first_half_stress, obj.second_half_stress, tone),
        )

    @admin.display(description="AI answers")
    def ai_answers(self, obj):
        if not obj.ai_runs:
            return "—"
        return format_html_join(
            "",
            "<p><strong>{}.</strong> {} * {}</p>",
            ((i, run.get("first_half", ""), run.get("second_half", "")) for i, run in enumerate(obj.ai_runs, 1)),
        )

    def save_model(self, request, obj, form, change):
        stress_changed = {"first_half_stress", "second_half_stress"} & set(form.changed_data)
        if change and stress_changed and "status" not in form.changed_data:
            obj.status = PsalmVersePointing.APPROVED
        super().save_model(request, obj, form, change)

    @admin.action(description="Approve the selected pointings")
    def approve(self, request, queryset):
        count = queryset.update(status=PsalmVersePointing.APPROVED)
        self.message_user(request, f"Approved {count}.")

    @admin.action(description="Mark the selected pointings as needing review")
    def mark_needs_review(self, request, queryset):
        count = queryset.update(status=PsalmVersePointing.NEEDS_REVIEW)
        self.message_user(request, f"Marked {count} for review.")


admin.site.register(Psalm, PsalmAdmin)
admin.site.register(PsalmVersePointing, PsalmVersePointingAdmin)
admin.site.register(PsalmVerse, PsalmVerseAdmin)
admin.site.register(PsalmTopic, PsalmTopicAdmin)
