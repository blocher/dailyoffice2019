# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import MovieNight, MovieVoter, MovieRankedVote, MovieCandidate, MovieBallot


@admin.register(MovieNight)
class MovieNightAdmin(admin.ModelAdmin):
    list_display = ("uuid", "created", "updated", "movie_date")
    list_filter = ("created", "updated", "movie_date")


@admin.register(MovieVoter)
class MovieVoterAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "created",
        "updated",
        "first_name",
        "last_name",
        "email",
    )
    list_filter = ("created", "updated")


@admin.register(MovieRankedVote)
class MovieRankedVoteAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "created",
        "updated",
        "rank",
        "ballot",
        "candidate",
    )
    list_filter = ("created", "updated", "ballot", "candidate")


@admin.register(MovieCandidate)
class MovieCandidateAdmin(admin.ModelAdmin):
    list_display = ("uuid", "created", "updated", "imdb_id", "movie_night")
    list_filter = ("created", "updated", "movie_night")


@admin.register(MovieBallot)
class MovieBallotAdmin(admin.ModelAdmin):
    list_display = ("uuid", "created", "updated", "voter", "movie_night")
    list_filter = ("created", "updated", "voter", "movie_night")
