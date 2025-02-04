import re

from django.contrib.postgres.fields import ArrayField
from django.db import models
from pyrankvote import Ballot

from churchcal.base_models import BaseModel
from standrew.helpers import get_election_results, serialize_election_result
from website.settings import SITE_ADDRESS


class MovieNight(BaseModel):
    movie_date = models.DateField()
    movie_results = models.JSONField(blank=True, null=True)

    def election_closed(self):
        from standrew.utils import get_today

        now = get_today()
        today = now.date()
        if self.movie_date < today:
            return True
        if self.movie_date > today:
            return False
        return now.hour >= 12

    def get_result(self, vetoes=True):
        result = get_election_results(self, vetoes)
        if self.election_closed() and not self.movie_results:
            self.movie_results = serialize_election_result(result)
            self.save()
        return result


class MovieVoter(BaseModel):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField()

    def __str__(self):
        return "{} {} ({})".format(self.first_name, self.last_name, self.email)


class MovieRankedVote(BaseModel):
    rank = models.PositiveIntegerField(default=0)
    ballot = models.ForeignKey("MovieBallot", on_delete=models.SET_NULL, null=True, blank=True)
    candidate = models.ForeignKey("MovieCandidate", on_delete=models.SET_NULL, null=True, blank=True)


class MovieCandidate(BaseModel):
    MOVIE_SERVICES = (
        ("amazon_prime", "Amazon Prime"),
        ("apple_tv_plus", "Apple TV Plus"),
        ("disney_plus", "Disney Plus"),
        ("hbo_max", "HBO Max"),
        ("hoopla", "Hoopla"),
        ("hulu", "Hulu"),
        ("netflix", "Netflix"),
        ("other", "Other"),
    )
    LIKELIHOOD_CHOICES = (
        (100, "I am definitely coming"),
        (75, "I will probably come"),
        (50, "50/50 at this point"),
        (25, "I most likely won't come"),
        (0, "I do not plan to come"),
        (-1, "Not Answered"),
    )
    movie_night = models.ForeignKey("MovieNight", on_delete=models.SET_NULL, null=True, blank=True)
    movie_service = models.CharField(
        max_length=256, verbose_name="Service Where This Movie is Available", choices=MOVIE_SERVICES
    )
    recommended_reason = models.TextField(blank=True, null=True)
    likelihood_of_coming = models.IntegerField(choices=LIKELIHOOD_CHOICES, default=-1)
    movie_voter = models.ForeignKey(
        "MovieVoter", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Who are you?"
    )
    imdb_id = models.ForeignKey("MovieDetails", on_delete=models.SET_NULL, blank=True, null=True, to_field="imdb_id")

    def __init__(self, name=None, *args, **kwargs):
        if name:
            args = (name,) + args
            kwargs["imdb_id"] = name
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.imdb_id.movie_details["fields"]["title"]

    def __repr__(self) -> str:
        return "<MovieCandidate('%s')>" % self.imdb_id.imdb_id

    def __hash__(self):
        return hash(self.imdb_id)

    def __eq__(self, other) -> bool:
        if other is None:
            return False

        return self.imdb_id == other.imdb_id

    @property
    def name(self):
        return self.imdb_id.movie_details["fields"]["title"]

    @property
    def service(self):
        return self.movie_service.capitalize().replace("_", " ")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        from standrew.utils import send_movie_email

        adding = self._state.adding
        result = super().save(force_insert, force_update, using, update_fields)
        if adding:
            subject = "{} {} has nominated {}".format(
                self.movie_voter.first_name, self.movie_voter.last_name, self.imdb_id.title
            )
            title = self.imdb_id.title
            rsvp = dict(self.LIKELIHOOD_CHOICES)[self.likelihood_of_coming]
            link = "{}/standrew/movies/results/{}".format(SITE_ADDRESS, self.movie_night_id)
            message = "{}\n<br>{}\n<br>{}".format(title, rsvp, link)
            send_movie_email(subject, message, "blocher@gmail.com")
        return result


class MovieBallot(BaseModel):
    LIKELIHOOD_CHOICES = (
        (100, "I am definitely coming"),
        (75, "I will most likely come"),
        (50, "I'm not sure (greater than 50/50 chance at this point)"),
    )

    voter = models.ForeignKey("MovieVoter", on_delete=models.SET_NULL, null=True, blank=True)
    movie_night = models.ForeignKey("MovieNight", on_delete=models.SET_NULL, null=True, blank=True)
    likelihood_of_coming = models.IntegerField(choices=LIKELIHOOD_CHOICES, default=-1)

    @property
    def rsvp(self):
        choices = dict(self.LIKELIHOOD_CHOICES)
        try:
            return choices[self.likelihood_of_coming]
        except KeyError:
            return "Unknown"

    def get_ballot(self, vetoes=None):
        return Ballot(
            [
                vote.candidate
                for vote in self.movierankedvote_set.order_by("rank").all()
                if vote.candidate_id not in vetoes
            ]
        )


class MovieDetails(BaseModel):
    imdb_id = models.CharField(max_length=256, unique=True)
    movie_details = models.JSONField(null=True, blank=True)

    @property
    def title(self):
        return self.movie_details["fields"]["title"]


class MovieVeto(BaseModel):
    voter = models.ForeignKey("MovieVoter", on_delete=models.SET_NULL, null=True, blank=True)
    candidate = models.ForeignKey("MovieCandidate", on_delete=models.SET_NULL, null=True, blank=True)


class BibleStudyDay(BaseModel):
    date = models.DateField(blank=True, null=True)

    jesus_story_book_number = models.PositiveSmallIntegerField(blank=True, null=True)
    jesus_story_book_title = models.CharField(max_length=512, blank=True, null=True)
    jesus_story_book_summary = models.TextField(blank=True, null=True)
    jesus_story_book_content = models.TextField(blank=True, null=True)
    passage_title = models.CharField(max_length=512, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    intersection = models.TextField(blank=True, null=True)
    study_questions = ArrayField(models.CharField(max_length=512), blank=True, null=True)
    practical_questions = ArrayField(models.CharField(max_length=512), blank=True, null=True)
    reflection = models.TextField(blank=True, null=True)
    quote = models.JSONField(blank=True, null=True)

    @property
    def passage_string(self):
        return ", ".join([passage.bible_study_passage.passage for passage in self.biblestudydaypassage_set.all()])

    def formatted_reflection(self):
        if not self.reflection:
            return ""
        return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", self.reflection.replace("\n", "<br>"))


class BibleStudyDayPassage(BaseModel):
    bible_study_day = models.ForeignKey("BibleStudyDay", on_delete=models.CASCADE)
    bible_study_passage = models.ForeignKey("BibleStudyPassage", on_delete=models.CASCADE)


class BibleStudyPassage(BaseModel):
    passage = models.CharField(max_length=256)
    text = models.TextField(blank=True, null=True)
    html = models.TextField(blank=True, null=True)
    headings = ArrayField(models.CharField(max_length=512), blank=True, null=True)
    extracted_headings = ArrayField(models.CharField(max_length=512), blank=True, null=True)
    theme = models.TextField(blank=True, null=True)
    four_senses = models.JSONField(blank=True, null=True)
    background = models.TextField(blank=True, null=True)
    primary_sources = models.JSONField(blank=True, null=True)
    interesting_points = models.TextField(blank=True, null=True)
    study_questions = ArrayField(models.CharField(max_length=512), blank=True, null=True)
    practical_questions = ArrayField(models.CharField(max_length=512), blank=True, null=True)
    reflection = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    primary_verse = models.JSONField(blank=True, null=True)

    def formatted_background(self):
        if not self.background:
            return ""
        return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", self.background.replace("\n", "<br>"))

    def formatted_interesting_points(self):
        if not self.interesting_points:
            return ""
        return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", self.interesting_points.replace("\n", "<br>"))

    def formatted_reflection(self):
        if not self.reflection:
            return ""
        return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", self.reflection.replace("\n", "<br>"))

    def formatted_html(self):
        if not self.html:
            return ""
        return (
            self.html.replace("<h1", "<h5")
            .replace("<h2", "<h5")
            .replace("<h3", "<h5")
            .replace("<h4", "<h5")
            .replace("</h1", "</h5")
            .replace("</h2", "</h5")
            .replace("</h3", "</h5")
            .replace("</h4", "</h5")
        )
