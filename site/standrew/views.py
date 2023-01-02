import json
import operator
from datetime import timedelta
from functools import reduce
from itertools import groupby
from math import ceil, floor
from types import SimpleNamespace

import requests
from cachetools.func import lru_cache
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.forms import ModelForm
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.generic import CreateView
from standrew.email import weekly_email, CommemorationDailyEmailModule, WeeklyMeetingEmailModule
from standrew.models import (
    MovieCandidate,
    MovieVoter,
    MovieBallot,
    MovieDetails,
    MovieRankedVote,
    MovieVeto,
    MovieNight,
)
from standrew.utils import (
    get_movie_night,
    check_if_nominations_open,
    get_friday,
    check_if_voting_open,
    CandidateResultDecorator,
    get_today,
    send_movie_email,
)
from website.settings import YOUTUBE_API_KEY, IMDB_API_KEY, UTELLY_API_KEY, OMDB_API_KEY, SITE_ADDRESS


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
    html = render_to_string("standrew/movie_candidate_success.html")
    return HttpResponse(html)


def movie_night_results(request, movie_night):
    vetos = MovieVeto.objects.filter(candidate__movie_night=movie_night).select_related("voter", "candidate").all()
    veto_ids = [veto.candidate.pk for veto in vetos]

    movie_night = (
        MovieNight.objects.prefetch_related(
            Prefetch(
                "movieballot_set",
                queryset=MovieBallot.objects.order_by("-likelihood_of_coming", "voter__last_name", "voter__first_name")
                .prefetch_related(
                    Prefetch(
                        "movierankedvote_set",
                        queryset=MovieRankedVote.objects.select_related("candidate__imdb_id").order_by("rank"),
                        to_attr="votes",
                    )
                )
                .prefetch_related(
                    Prefetch(
                        "movierankedvote_set",
                        queryset=MovieRankedVote.objects.select_related("candidate__imdb_id")
                        .order_by("rank")
                        .exclude(candidate__pk__in=veto_ids),
                        to_attr="no_veto_votes",
                    )
                )
                .select_related("voter"),
                to_attr="ballots",
            )
        )
        .prefetch_related(
            Prefetch(
                "moviecandidate_set",
                queryset=MovieCandidate.objects.order_by(
                    "-likelihood_of_coming", "movie_voter__last_name", "movie_voter__first_name"
                ).select_related("imdb_id", "movie_voter"),
                to_attr="candidates",
            )
        )
        .get(pk=movie_night)
    )

    no_rsvp_ids = [ballot.voter_id for ballot in movie_night.ballots]
    rsvps = {
        k: [ballot.voter for ballot in g] for k, g in groupby(movie_night.ballots, lambda x: x.likelihood_of_coming)
    }
    rsvps["na"] = MovieVoter.objects.exclude(pk__in=no_rsvp_ids).order_by("last_name", "first_name").all()

    candidates_no_rsvp_ids = [candidate.movie_voter_id for candidate in movie_night.candidates]
    candidate_rsvps = {
        k: [candidate.movie_voter for candidate in g]
        for k, g in groupby(movie_night.candidates, lambda x: x.likelihood_of_coming)
    }
    candidate_rsvps["na"] = (
        MovieVoter.objects.exclude(pk__in=candidates_no_rsvp_ids).order_by("last_name", "first_name").all()
    )

    results = movie_night.get_result()
    no_veto_results = movie_night.get_result(vetoes=False)

    for i, election_round in enumerate(results.rounds):
        for j, candidate in enumerate(election_round.candidate_results):
            results.rounds[i].candidate_results[j] = CandidateResultDecorator(candidate)

    for i, election_round in enumerate(no_veto_results.rounds):
        for j, candidate in enumerate(election_round.candidate_results):
            no_veto_results.rounds[i].candidate_results[j] = CandidateResultDecorator(candidate)

    html = render_to_string(
        "standrew/movie_results.html",
        {
            "closed": movie_night.election_closed(),
            "admin": request.user.is_authenticated,
            "ballots": movie_night.ballots,
            "rsvps": rsvps,
            "candidate_rsvps": candidate_rsvps,
            "vetos": vetos,
            "winner": results.winner.imdb_id.movie_details if results.winner else None,
            "full_winner": results.winner if results.winner else None,
            "rounds": results.rounds,
            "no_veto_rounds": no_veto_results.rounds,
            "number_to_win": floor(float(len(movie_night.ballots)) / 2) + 1,
            "number_of_candidates": len(movie_night.ballots),
            "candidates": sorted(movie_night.candidates, key=lambda t: t.imdb_id.title),
            "date": movie_night.movie_date,
            "hide_warnings": True,
        },
    )
    return HttpResponse(html)


def movie_vote_success(request):
    html = render_to_string("standrew/movie_vote_success.html")
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
            if locations:
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
            return None

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
        today = get_today()
        one_week_ago = today - timedelta(days=7)
        existing_record = MovieDetails.objects.get(imdb_id=imdb_id, updated__gte=one_week_ago)
        context = existing_record.movie_details
    except MovieDetails.DoesNotExist:
        context = {
            "omdb": omdb(imdb_id),
            "utelly": utelly(imdb_id),
            "youtube": youtube(imdb_id),
            "imdb": imdb(imdb_id),
        }
        context["fields"] = standardized_fields(context)
        details = MovieDetails.objects.get_or_create(imdb_id=imdb_id)[0]
        details.movie_details = context
        details.save()
    return context


def get_movie_details_html(imdb_id, hide_warnings=True):
    context = get_movie_details(imdb_id)
    context["hide_warnings"] = hide_warnings
    return render_to_string("standrew/movie_preview.html", context)


def movie_details(request, imdb_id):
    return HttpResponse(get_movie_details_html(imdb_id, hide_warnings=False))

    # Or, JSON
    # return HttpResponse(get_movie_details_html(imdb_id))


class MovieCandidateForm(ModelForm):
    class Meta:
        model = MovieCandidate
        fields = [
            "imdb_id",
            "movie_service",
            "recommended_reason",
            "likelihood_of_coming",
            "movie_voter",
            "movie_night",
        ]

    def clean(self):
        cleaned_data = super().clean()

        duplicates = MovieCandidate.objects.filter(
            imdb_id_id=cleaned_data.get("imdb_id"), movie_night_id=cleaned_data.get("movie_night")
        ).count()
        if duplicates:
            raise ValidationError("This movie has already been nominated by someone else. Please pick another movie.")

        return cleaned_data


class MovieCandidateCreate(CreateView):
    model = MovieCandidate
    success_url = "/standrew/movies/nominate/success/"
    form_class = MovieCandidateForm

    def get_voter(self):
        try:
            return MovieVoter.objects.get(pk=self.kwargs["voter"])
        except MovieVoter.DoesNotExist:
            return False

    def already_nominated(self):
        return MovieCandidate.objects.filter(movie_night=get_movie_night(), movie_voter=self.get_voter()).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Nominate a Movie"
        context["open"] = check_if_nominations_open()
        context["date"] = get_friday()
        context["movie_night"] = get_movie_night()
        context["movie_voter"] = self.get_voter()
        context["already_nominated"] = self.already_nominated()
        return context

    def get(self, request, *args, **kwargs):
        if not self.get_voter():
            raise Http404("Voter does not exist")

        return super().get(request, *args, **kwargs)


class MovieBallotCreate(CreateView):
    model = MovieBallot
    fields = ["voter", "movie_night", "likelihood_of_coming"]
    success_url = "/standrew/movies/vote/success/"

    def get_voter(self):
        try:
            return MovieVoter.objects.get(pk=self.kwargs["voter"])
        except MovieVoter.DoesNotExist:
            return False

    def already_voted(self):
        return MovieBallot.objects.filter(movie_night=get_movie_night(), voter=self.get_voter()).exists()

    def get_candidates(self):
        candidates = MovieCandidate.objects.order_by("?").filter(movie_night=get_movie_night())
        return [
            {
                "pk": candidate.pk,
                "movie": get_movie_details_html(candidate.imdb_id_id),
                "data": get_movie_details(candidate.imdb_id_id),
                "nominator": candidate.movie_voter,
                "reason": candidate.recommended_reason,
                "service": candidate.movie_service.replace("_", " ").title(),
            }
            for candidate in candidates
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Vote for your stinkin' movie"
        context["open"] = check_if_voting_open()
        context["date"] = get_friday()
        context["movie_night"] = get_movie_night()
        context["movie_voter"] = self.get_voter()
        context["already_voted"] = self.already_voted()
        context["candidates"] = self.get_candidates()
        context["hide_warnings"] = True
        return context

    def get(self, request, *args, **kwargs):
        if not self.get_voter():
            raise Http404("Voter does not exist")

        return super().get(request, *args, **kwargs)

    def send_voted_email(self):
        from standrew.utils import send_movie_email

        ballot = (
            MovieBallot.objects.prefetch_related(
                Prefetch("movierankedvote_set", queryset=MovieRankedVote.objects.order_by("rank"), to_attr="votes")
            )
            .order_by("-created")
            .first()
        )
        subject = "{} {} has voted".format(ballot.voter.first_name, ballot.voter.last_name)

        votes = ""
        for ranked_vote in ballot.votes:
            votes = "{}<br>".format(votes + ranked_vote.candidate.imdb_id.title)

        rsvp = dict(ballot.LIKELIHOOD_CHOICES)[ballot.likelihood_of_coming]
        link = "{}/standrew/movies/results/{}".format(SITE_ADDRESS, ballot.movie_night_id)
        message = "{}\n<br>{}\n<br><br><br>{}".format(rsvp, link, votes)
        send_movie_email(subject, message, "blocher@gmail.com")

    def post(self, request, *args, **kwargs):
        candidate_count = MovieCandidate.objects.filter(movie_night=get_movie_night()).count()
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
        self.send_voted_email()
        return result
