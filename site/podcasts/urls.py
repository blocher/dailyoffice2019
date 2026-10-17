from django.urls import path

from podcasts.views import (
    CustomPodcastChaptersView,
    CustomPodcastCreateView,
    CustomPodcastEpisodeAudioView,
    CustomPodcastFeedView,
    CustomPodcastTranscriptView,
    PodcastArtworkView,
    PodcastCatalogView,
    PodcastChaptersView,
    PodcastEpisodeAudioView,
    PodcastFeedView,
    PodcastTranscriptView,
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
    *(
        path(
            f"podcasts/transcripts/<slug:slug>/<int:year>-<int:month>-<int:day>.{extension}",
            PodcastTranscriptView.as_view(),
            {"extension": extension},
            name=f"podcast_transcript_{extension}",
        )
        for extension in ("vtt", "srt")
    ),
    # EXPERIMENTAL custom podcasts (podcasts/custom.py): private feeds behind a token.
    path("api/v1/podcasts/custom", CustomPodcastCreateView.as_view(), name="custom_podcast_create"),
    path("podcasts/custom/<slug:token>.xml", CustomPodcastFeedView.as_view(), name="custom_podcast_feed"),
    path(
        "podcasts/custom/<slug:token>/<int:year>-<int:month>-<int:day>.mp3",
        CustomPodcastEpisodeAudioView.as_view(),
        name="custom_podcast_episode_audio",
    ),
    path(
        "podcasts/custom/<slug:token>/<int:year>-<int:month>-<int:day>.json",
        CustomPodcastChaptersView.as_view(),
        name="custom_podcast_chapters",
    ),
    *(
        path(
            f"podcasts/custom/<slug:token>/<int:year>-<int:month>-<int:day>.{extension}",
            CustomPodcastTranscriptView.as_view(),
            {"extension": extension},
            name=f"custom_podcast_transcript_{extension}",
        )
        for extension in ("vtt", "srt")
    ),
]
