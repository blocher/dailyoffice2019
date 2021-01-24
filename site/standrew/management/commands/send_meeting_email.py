from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from html2text import html2text
from standrew.email import WeeklyMeetingEmailModule
from website.settings import DEBUG


class Command(BaseCommand):
    help = "Send weekly St. Andrew email"

    def handle(self, *args, **options):

        module = WeeklyMeetingEmailModule()
        if not module.should_send:
            return
        for meeting in module.data:
            subject = module.individual_subject(meeting)
            content = module.individual_render(meeting)
            context = {"modules": [content]}
            html_message = render_to_string("emails/weekly_email.html", context)
            message = html2text(html_message)
            email_from = '"Community of St. Andrew" <community-of-st-andrew-all@googlegroups.com>'
            recipient_list = meeting["to_addresses"]
            if DEBUG:
                print(recipient_list)
                recipient_list = ["blocher@gmail.com"]
            bcc_list = ["blocher@gmail.com"]
            reply_to = meeting["to_addresses"]

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
