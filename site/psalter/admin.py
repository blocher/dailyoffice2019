from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q

from psalter.models import PsalmTopic, PsalmVerse


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
        print("am here", self.value())
        value = int(self.value())
        if value == 1:
            print("does match")
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


admin.site.register(PsalmVerse, PsalmVerseAdmin)
admin.site.register(PsalmTopic, PsalmTopicAdmin)
