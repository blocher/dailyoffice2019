from datetime import timedelta

import kronos
import pytz
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from html2text import html2text

from standrew.models import BibleStudyDay
from standrew.utils import get_today
from standrew.views import bible_study_passage_email
from website.settings import DEBUG


def is_first_or_third_tuesday(date):
    if date.weekday() != 1:  # 1 is Tuesday
        return False
    first_day_of_month = date.replace(day=1)
    first_tuesday = first_day_of_month + timedelta(days=(1 - first_day_of_month.weekday() + 7) % 7)
    third_tuesday = first_tuesday + timedelta(weeks=2)
    return date == first_tuesday or date == third_tuesday


def check_tuesday():
    today = get_today()
    if today.weekday() == 1:  # 1 is Tuesday
        return is_first_or_third_tuesday(today)
    else:
        next_tuesday = today + timedelta(days=(1 - today.weekday() + 7) % 7)
        return is_first_or_third_tuesday(next_tuesday)


@kronos.register("0 17 * * 1")
@kronos.register("0 8 * * 6")
class Command(BaseCommand):
    help = "Send weekly St. Andrew Bible Study email"

    def handle(self, *args, **options):

        if not check_tuesday():
            print("not correct tuesday")
            return
        today = get_today().astimezone(pytz.timezone("US/Eastern")).replace(hour=0, minute=0, second=0, microsecond=0)
        days = (
            BibleStudyDay.objects.order_by("date", "jesus_story_book_number", "created").filter(date__gte=today).all()
        )
        if days:
            day = days[0]
        else:
            day = BibleStudyDay.objects.order_by("date", "jesus_story_book_number", "created").first()

        subject = "St. Andrew's Bible Study: " + day.passage_string
        html_message = bible_study_passage_email(id=day.pk, raw_html=True, subject=subject)
        message = html2text(html_message)
        email_from = '"Community of St. Andrew" <community-of-st-andrew-all@googlegroups.com>'
        recipient_list = ["community-of-st-andrew-all@googlegroups.com"]
        if DEBUG:
            recipient_list = ["blocher@gmail.com", "ealocher@gmail.com"]
        bcc_list = ["blocher@gmail.com"]
        reply_to = ["community-of-st-andrew-all@googlegroups.com"]

        email = EmailMultiAlternatives(
            subject,
            message,
            email_from,
            recipient_list,
            bcc_list,
            reply_to=reply_to,
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
