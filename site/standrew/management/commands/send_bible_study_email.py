import kronos
import pytz
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.utils import timezone
from html2text import html2text

from standrew.models import BibleStudyDay
from standrew.views import bible_study_passage_email
from website.settings import DEBUG


@kronos.register("0 17 * * 1")
@kronos.register("0 8 * * 6")
class Command(BaseCommand):
    help = "Send weekly St. Andrew Bible Study email"

    def handle(self, *args, **options):
        today = (
            timezone.now().astimezone(pytz.timezone("US/Eastern")).replace(hour=0, minute=0, second=0, microsecond=0)
        )
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
