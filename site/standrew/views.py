import json
import datetime
import operator
from functools import reduce
from types import SimpleNamespace

import requests
from cachetools.func import lru_cache
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import CreateView
from standrew.email import weekly_email, CommemorationDailyEmailModule, WeeklyMeetingEmailModule
from standrew.models import (
    MovieCandidate,
    MovieNight,
    MovieVoter,
    MovieBallot,
    MovieDetails,
    MovieRankedVote,
    MovieVeto,
)
from website.settings import YOUTUBE_API_KEY, IMDB_API_KEY, UTELLY_API_KEY, OMDB_API_KEY


def current_email(request):
    modules = [module for module in weekly_email()]
    content = [module.render() for module in modules]
    context = {"modules": content, "heading": "The Week Ahead"}
    subjects = ["; ".join(module.subjects) for module in modules if module.subjects]
    subject = "; ".join(subjects)

    html = subject + render_to_string("emails/weekly_email.html", context)
    return HttpResponse(html)


def feast_email(request):
    modules = [CommemorationDailyEmailModule()]
    content = [module.render() for module in modules]
    context = {"modules": content}

    html = render_to_string("emails/weekly_email.html", context)
    return HttpResponse(html)


def meeting_email(request):
    module = WeeklyMeetingEmailModule()
    renderings = module.render()
    html = mark_safe("<br>".join(renderings))
    context = {"modules": [html]}
    html = "<h1>{}</h1>".format(module.subject) + render_to_string("emails/weekly_email.html", context)
    return HttpResponse(html)


def movie_search(request, search_field):
    search_field = search_field.lower()
    initial = search_field[:1]

    result = requests.get("https://v2.sg.media-imdb.com/suggestion/titles/{}/{}.json".format(initial, search_field))
    content = result.content.decode("utf-8")
    results = json.loads(content, object_hook=lambda d: SimpleNamespace(**d))

    results = {
        "items": [
            {"id": movie.id, "title": "{} ({})".format(movie.l, movie.y if hasattr(movie, "y") else "?")}
            for movie in results.d
        ]
    }
    return HttpResponse(json.dumps(dict(results)))


def movie_candidate_success(request):
    html = render_to_string("standrew/movie_success.html")
    return HttpResponse(html)


def get_from_dict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)


def get_movie_details_from_dict(context, possibilities):
    value = None
    for possibility in possibilities:
        try:
            value = get_from_dict(context, possibility)
        except (AttributeError, KeyError):
            pass
        if value:
            return value
    return value


def get_movie_details(imdb_id):
    def standardized_fields(context):
        def title():
            return get_movie_details_from_dict(
                context, [["omdb", "Title"], ["imdb", "title"], ["utelly", "collection", "name"]]
            )

        def year():
            return get_movie_details_from_dict(context, [["omdb", "Year"], ["imdb", "year"]])

        def rating():
            return get_movie_details_from_dict(context, [["omdb", "Rated"], ["imdb", "rated"]])

        def genre():
            value = get_movie_details_from_dict(context, [["imdb", "genres"], ["omdb", "Genre"]])
            if type(value) is list:
                value = ", ".join(value)
            return value

        def runtime():
            value = get_movie_details_from_dict(context, [["omdb", "Runtime"], ["imdb", "runtime"]])
            try:
                value = int(value.replace("min", ""))
                hours = int(value / 60)
                minutes = value % 60
                if hours:
                    return "{} hours {} minutes".format(hours, minutes)
                return "{} minutes".format(minutes)
            except Exception:
                return value

        def poster():
            return get_movie_details_from_dict(context, [["omdb", "Poster"], ["utelly", "collection", "picture"]])

        def plot():
            return get_movie_details_from_dict(context, [["omdb", "Plot"], ["imdb", "description"]])

        def trailer():
            return get_movie_details_from_dict(context, [["imdb", "youtube_trailer_key"], ["youtube"]])

        def services():
            locations = get_movie_details_from_dict(context, [["utelly", "collection", "locations"]])
            locations = [
                location
                for location in locations
                if location["name"]
                in (
                    "AmazonPrimeVideoIVAUS",
                    "NetflixIVAUS",
                    "DisneyPlusIVAUS",
                    "HuluIVAUS",
                    "AppleTvPlusIVAUS",
                    "HBOMaxIVAUS",
                )
            ]
            return locations

        def ratings():
            value = get_movie_details_from_dict(context, [["omdb", "Ratings"], ["imdb", "imdb_rating"]])
            if value:
                if type(value) is list:
                    for i, rating in enumerate(value):
                        if rating["Source"] == "Internet Movie Database":
                            value[i]["Source"] = "IMDb"
                else:
                    value = [
                        {"Value": "{}/10".format(value), "Source": "IMDb"},
                    ]
            return value

        return {
            "title": title(),
            "year": year(),
            "rating": rating(),
            "genre": genre(),
            "runtime": runtime(),
            "poster": poster(),
            "plot": plot(),
            "trailer": trailer(),
            "services": services(),
            "ratings": ratings(),
            "imdb_id": imdb_id,
        }

    @lru_cache(maxsize=None)
    def omdb(imdb_id):
        try:
            result = requests.get("http://www.omdbapi.com/?apikey={}&plot=full&i={}".format(OMDB_API_KEY, imdb_id))
            content = result.content.decode("utf-8")
            return json.loads(content)
        except:
            return {"imdbID": imdb_id, "error": True}

    @lru_cache(maxsize=None)
    def utelly(imdb_id):
        try:
            url = "https://utelly-tv-shows-and-movies-availability-v1.p.rapidapi.com/idlookup"
            querystring = {"source_id": imdb_id, "source": "imdb", "country": "us"}
            headers = {
                "x-rapidapi-key": UTELLY_API_KEY,
                "x-rapidapi-host": "utelly-tv-shows-and-movies-availability-v1.p.rapidapi.com",
            }
            result = requests.request("GET", url, headers=headers, params=querystring)
            content = result.content.decode("utf-8")
            content = json.loads(content)
            return content
        except:
            return []

    @lru_cache(maxsize=None)
    def imdb(imdb_id):
        url = "https://movies-tvshows-data-imdb.p.rapidapi.com/"

        querystring = {"type": "get-movie-details", "imdb": imdb_id}

        headers = {
            "x-rapidapi-key": IMDB_API_KEY,
            "x-rapidapi-host": "movies-tvshows-data-imdb.p.rapidapi.com",
        }

        result = requests.request("GET", url, headers=headers, params=querystring)
        content = result.content.decode("utf-8")
        content = json.loads(content)
        return content

    @lru_cache(maxsize=None)
    def youtube(imdb_id):
        try:
            params = {
                "regionCode": "US",
                "relevanceLanguage": "en",
                "type": "video",
                "part": "snippet",
                "q": "{} trailer".format(omdb(imdb_id)["Title"]),
                "topicId": "/m/02vxn",
                "key": YOUTUBE_API_KEY,
            }
            url = "https://www.googleapis.com/youtube/v3/search"
            result = requests.request("GET", url, params=params)
            content = result.content.decode("utf-8")
            content = json.loads(content)
            return content["items"][0]["id"]["videoId"]
        except Exception as e:
            print(e)
            return ""

    try:
        existing_record = MovieDetails.objects.get(imdb_id=imdb_id)
        context = existing_record.movie_details
    except MovieDetails.DoesNotExist:
        context = {
            "omdb": omdb(imdb_id),
            "utelly": utelly(imdb_id),
            "youtube": youtube(imdb_id),
            "imdb": imdb(imdb_id),
        }
        context["fields"] = standardized_fields(context)
        MovieDetails.objects.create(imdb_id=imdb_id, movie_details=context)
    return context


def get_movie_details_html(imdb_id):
    context = get_movie_details(imdb_id)
    return render_to_string("standrew/movie_preview.html", context)


def movie_details(request, imdb_id):
    return HttpResponse(get_movie_details_html(imdb_id))

    # Or, JSON
    # return HttpResponse(get_movie_details_html(imdb_id))


def get_today():
    # if settings.DEBUG:
    #     return datetime.datetime.strptime("{} {} {}".format(2, 23, 2021), "%m %d %Y")
    return timezone.localtime(timezone.now())


class MovieCandidateCreate(CreateView):
    model = MovieCandidate
    fields = ["imdb_id", "movie_service", "movie_voter", "movie_night"]
    success_url = "/standrew/movies/nominate/success/"

    def get_friday(self):
        today = get_today()
        today_time = today + datetime.timedelta((4 - today.weekday()) % 7)
        return today_time.date()

    def next_friday_is_movie_night(self):
        first_friday = datetime.datetime.strptime("Jan 15 2021 12:00AM", "%b %d %Y %I:%M%p").date()
        current_friday = self.get_friday()
        difference = (current_friday - first_friday).days / 7
        if difference % 4 == 0:
            return False  # game night
        if difference % 2 == 0:
            return True
        return False

    def check_if_open(self):
        if not self.next_friday_is_movie_night():
            return False
        weekday = get_today().weekday()
        if weekday not in [0, 1, 2, 3, 6]:
            return False
        if weekday == 3:
            if get_today().hour >= 12:
                return False
        return True

    def get_movie_night(self):
        if not self.check_if_open():
            return False
        friday = self.get_friday()
        return MovieNight.objects.get_or_create(movie_date=friday)[0]

    def get_voter(self):
        try:
            return MovieVoter.objects.get(pk=self.kwargs["voter"])
        except MovieVoter.DoesNotExist:
            return False

    def already_nominated(self):
        return MovieCandidate.objects.filter(movie_night=self.get_movie_night(), movie_voter=self.get_voter()).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Nominate a Movie"
        context["open"] = self.check_if_open()
        context["date"] = self.get_friday()
        context["movie_night"] = self.get_movie_night()
        context["movie_voter"] = self.get_voter()
        context["already_nominated"] = self.already_nominated()
        return context

    def get(self, request, *args, **kwargs):
        if not self.get_voter():
            raise Http404("Voter does not exist")

        return super().get(request, *args, **kwargs)


class MovieBallotCreate(CreateView):
    model = MovieBallot
    fields = ["voter", "movie_night"]
    success_url = "/standrew/movies/nominate/success/"

    def get_friday(self):
        today = get_today()
        today_time = today + datetime.timedelta((4 - today.weekday()) % 7)
        return today_time.date()

    def next_friday_is_movie_night(self):
        first_friday = datetime.datetime.strptime("Jan 15 2021 12:00AM", "%b %d %Y %I:%M%p").date()
        current_friday = self.get_friday()
        difference = (current_friday - first_friday).days / 7
        print(difference)
        if difference % 4 == 0:
            return False  # game night
        if difference % 2 == 0:
            return True
        return False

    def check_if_open(self):
        if not self.next_friday_is_movie_night():
            return False
        weekday = get_today().weekday()
        if weekday not in [3, 4]:
            return False
        if weekday == 3:
            return get_today().hour > 12
        if weekday == 4:
            return get_today().hour < 12
        return False

    def get_movie_night(self):
        if not self.check_if_open():
            return False
        friday = self.get_friday()
        return MovieNight.objects.get_or_create(movie_date=friday)[0]

    def get_voter(self):
        try:
            return MovieVoter.objects.get(pk=self.kwargs["voter"])
        except MovieVoter.DoesNotExist:
            return False

    def already_voted(self):
        return MovieBallot.objects.filter(movie_night=self.get_movie_night(), voter=self.get_voter()).exists()

    def get_candidates(self):
        candidates = MovieCandidate.objects.order_by("?").filter(movie_night=self.get_movie_night())
        return [
            {
                "pk": candidate.pk,
                "movie": get_movie_details_html(candidate.imdb_id_id),
                "nominator": candidate.movie_voter,
                "data": get_movie_details(candidate.imdb_id_id),
                "nominator": candidate.movie_voter,
            }
            for candidate in candidates
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Vote for your stinkin' movie"
        context["open"] = self.check_if_open()
        context["date"] = self.get_friday()
        context["movie_night"] = self.get_movie_night()
        context["movie_voter"] = self.get_voter()
        context["already_voted"] = self.already_voted()
        context["candidates"] = self.get_candidates()
        return context

    def get(self, request, *args, **kwargs):
        if not self.get_voter():
            raise Http404("Voter does not exist")

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        candidate_count = MovieCandidate.objects.filter(movie_night=self.get_movie_night()).count()
        ballot = request.POST.get("ballot", "")
        votes = ballot.split(",")
        if len(votes) != candidate_count:
            raise ValidationError("You must rank order all of the movies.")
        vetos = request.POST.getlist("vetos")
        result = super().post(request, *args, **kwargs)
        for i, vote in enumerate(votes):
            MovieRankedVote.objects.create(rank=i, candidate_id=vote, ballot=self.object)
        for veto in vetos:
            candidate = MovieCandidate.objects.get(pk=veto)
            MovieVeto.objects.get_or_create(candidate=candidate, voter_id=self.object.voter_id)
        return result
