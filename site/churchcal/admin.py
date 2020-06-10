
from django.contrib import admin

from churchcal.models import Commemoration


class CommemorationAdmin(admin.ModelAdmin):
    list_display = ("name", "rank", "color")

    # def get_queryset(self, request):
    #     queryset = super().get_queryset(request)
    #     queryset = queryset.filter(name__contains="after Trinity")
    #     return queryset

admin.site.register(Commemoration, CommemorationAdmin)
