from django.contrib import admin

from podcasts.models import PodcastDirectoryListing, PodcastEpisode


@admin.register(PodcastEpisode)
class PodcastEpisodeAdmin(admin.ModelAdmin):
    list_display = ("title", "feed_slug", "date", "published_at", "duration", "file_size")
    list_filter = ("feed_slug",)
    search_fields = ("title", "summary")
    date_hierarchy = "date"
    # Published episodes are permanent; their audio and identity never change.
    readonly_fields = ("feed_slug", "date", "filename", "file_size", "duration", "guid", "created", "updated")


@admin.register(PodcastDirectoryListing)
class PodcastDirectoryListingAdmin(admin.ModelAdmin):
    list_display = ("feed_slug", "platform", "url", "order")
    list_filter = ("platform", "feed_slug")
