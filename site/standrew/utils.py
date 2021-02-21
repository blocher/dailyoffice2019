import datetime

import kronos
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from html2text import html2text
from standrew.models import MovieVoter, MovieCandidate, MovieNight
from website.settings import SITE_ADDRESS, ZOOM_LINK, DEBUG


def get_today():
    if DEBUG:
        return datetime.datetime.strptime("{} {} {}".format(2, 23, 2021), "%m %d %Y")
    return timezone.localtime(timezone.now())


def get_friday():
    today = get_today()
    today_time = today + datetime.timedelta((4 - today.weekday()) % 7)
    return today_time.date()


def next_friday_is_movie_night():
    first_friday = datetime.datetime.strptime("Jan 15 2021 12:00AM", "%b %d %Y %I:%M%p").date()
    current_friday = get_friday()
    difference = (current_friday - first_friday).days / 7
    if difference % 4 == 0:
        return False  # game night
    if difference % 2 == 0:
        return True
    return False


def get_movie_night():
    if not next_friday_is_movie_night():
        return False
    friday = get_friday()
    return MovieNight.objects.get_or_create(movie_date=friday)[0]


def check_if_nominations_open():
    if not next_friday_is_movie_night():
        return False
    weekday = get_today().weekday()
    if weekday not in [0, 1, 2, 3, 6]:
        return False
    if weekday == 3:
        if get_today().hour >= 12:
            return False
    return True


def check_if_voting_open():
    if not next_friday_is_movie_night():
        return False
    weekday = get_today().weekday()
    if weekday not in [3, 4]:
        return False
    if weekday == 3:
        return get_today().hour > 12
    if weekday == 4:
        return get_today().hour < 12
    return False


def send_movie_email(subject, message, email):
    email_from = '"Community of St. Andrew" <community-of-st-andrew-all@googlegroups.com>'
    bcc_list = ["blocher@gmail.com"]
    reply_to = [
        "community-of-st-andrew-all@googlegroups.com",
        "community-of-st-andrew-alumni@googlegroups.com",
    ]

    html_message = message
    text_message = html2text(message)

    recipient_list = [email]
    if DEBUG:
        recipient_list = ["blocher@gmail.com"]

    email = EmailMultiAlternatives(
        subject,
        text_message,
        email_from,
        recipient_list,
        bcc_list,
        reply_to=reply_to,
    )
    email.attach_alternative(html_message, "text/html")
    email.send()


@kronos.register("0 6 * * 3")
def send_movie_nomination_emails():
    if not next_friday_is_movie_night():
        return
    voters = MovieVoter.objects.all()
    for voter in voters:
        subject = "Movie Nominations open until Thursday at noon for this Friday's St. Andrew's Movie Night"
        context = {
            "nomination_link": "{}/standrew/movies/nominate/{}".format(SITE_ADDRESS, voter.uuid),
        }
        message = render_to_string("emails/movie_nominate.html", context)
        send_movie_email(subject, message, voter.email)


@kronos.register("0 12 * * 4")
def send_movie_vote_emails():
    voters = MovieVoter.objects.all()
    movie_night = MovieNight.objects.order_by("movie_date").filter(movie_date__gte=timezone.now()).first()
    candidates = MovieCandidate.objects.filter(movie_night=movie_night).all()
    for voter in voters:
        subject = "Movie Night Voting open until Friday at noon for this Friday's St. Andrew's Movie Night"
        context = {
            "voting_link": "{}/standrew/movies/vote/{}".format(SITE_ADDRESS, voter.uuid),
            "candidates": candidates,
        }
        message = render_to_string("emails/movie_vote.html", context)
        send_movie_email(subject, message, voter.email)


@kronos.register("0 12 * * 5")
def send_movie_results_emails():
    def send_message(voters, context):
        for voter in voters:
            subject = "Movie Night Winner: {} | See you at 8:45pm".format(context["winner"])
            message = render_to_string("emails/movie_result.html", context)
            send_movie_email(subject, message, voter.email)

    context = {
        "zoom_link": ZOOM_LINK,
        "slack_link": "",
    }

    movie_night = MovieNight.objects.order_by("movie_date").filter(movie_date__gte=timezone.now()).first()

    voters = MovieVoter.objects.all()
    if not voters:
        context["winner"] = "No one voted, so let's just show up and decide!"

    candidates = MovieCandidate.objects.filter(movie_night=movie_night).all()

    if len(candidates) == 0:
        context["winner"] = "No one made a nomination, so let's just show up and decide!"
        return send_message(voters, context)

    if len(candidates) == 1:
        context["winner"] = candidates[0].imdb_id.movie_details["details"]["Title"]
        return send_message(voters, context)

    results = movie_night.get_result()
    context["winner"] = results.get_winner()
    return send_message(voters, context)
