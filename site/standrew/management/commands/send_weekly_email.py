import kronos
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from html2text import html2text
from standrew.email import weekly_email
from website.settings import DEBUG


@kronos.register("0 18 * * 0")
class Command(BaseCommand):
    help = "Send weekly St. Andrew email"

    def handle(self, *args, **options):
        modules = [module for module in weekly_email()]
        content = [module.render() for module in modules]
        subjects = ["; ".join(module.subjects) for module in modules if module.subjects]
        subject = "; ".join(subjects)
        context = {"modules": content, "heading": "The Week Ahead"}

        html_message = render_to_string("emails/weekly_email.html", context)
        subject = "St. Andrew's Week Ahead: {}".format(subject)
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
