from django.urls import path

from podcasts.views import (
    PodcastArtworkView,
    PodcastCatalogView,
    PodcastChaptersView,
    PodcastEpisodeAudioView,
    PodcastFeedView,
)

# Feed, episode, and artwork URLs are public and permanent: podcast apps keep
# them forever. Add new routes; never change these.
urlpatterns = [
    path("api/v1/podcasts", PodcastCatalogView.as_view(), name="podcast_catalog"),
    path("podcasts/<slug:slug>.xml", PodcastFeedView.as_view(), name="podcast_feed"),
    path("podcasts/artwork/<slug:name>.jpg", PodcastArtworkView.as_view(), name="podcast_artwork"),
    path(
        "podcasts/chapters/<slug:slug>/<int:year>-<int:month>-<int:day>.json",
        PodcastChaptersView.as_view(),
        name="podcast_chapters",
    ),
    path("podcasts/episodes/<path:path>", PodcastEpisodeAudioView.as_view(), name="podcast_episode_audio"),
]
