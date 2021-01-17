from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from html2text import html2text
from standrew.email import weekly_email, CommemorationDailyEmailModule
from website.settings import DEBUG


class Command(BaseCommand):
    help = "Send weekly St. Andrew email"

    def handle(self, *args, **options):
        module = CommemorationDailyEmailModule()
        if not module.should_send:
            return
        content = module.render()
        subject = module.subject
        context = {"modules": [content]}

        html_message = render_to_string("emails/weekly_email.html", context)
        message = html2text(html_message)
        email_from = '"Community of St. Andrew" <community-of-st-andrew-all@googlegroups.com>'
        recipient_list = ["community-of-st-andrew-all@googlegroups.com"]
        if DEBUG:
            recipient_list = ["blocher@gmail.com"]
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
