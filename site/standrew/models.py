import pyrankvote
from churchcal.base_models import BaseModel
from django.db import models
from pyrankvote import Candidate, Ballot


class MovieNight(BaseModel):
    movie_date = models.DateField()

    def get_result(self):
        return pyrankvote.instant_runoff_voting(
            self.moviecandidate_set, [movie_ballot.get_ballot() for movie_ballot in self.movieballot_set]
        )


class MovieVoter(BaseModel):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField()


class MovieRankedVote(BaseModel):
    rank = models.PositiveIntegerField(default=0)
    ballot = models.ForeignKey("MovieBallot", on_delete=models.SET_NULL, null=True, blank=True)
    candidate = models.ForeignKey("MovieCandidate", on_delete=models.SET_NULL, null=True, blank=True)


class MovieCandidate(Candidate, BaseModel):
    def __init__(self, name="", *args, **kwargs):
        Candidate.__init__(self, name)
        BaseModel.__init__(self, *args, **kwargs)
        self.name = name

    name = models.CharField(max_length=256)
    movie_night = models.ForeignKey("MovieNight", on_delete=models.SET_NULL, null=True, blank=True)


class MovieBallot(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    voter = models.ForeignKey("MovieVoter", on_delete=models.SET_NULL, null=True, blank=True)
    movie_night = models.ForeignKey("MovieNight", on_delete=models.SET_NULL, null=True, blank=True)

    def get_ballot(self):
        return Ballot(self.movierankedvote_set)
