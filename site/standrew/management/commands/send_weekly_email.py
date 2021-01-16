from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from html2text import html2text
from standrew.email import weekly_email


class Command(BaseCommand):
    help = "Send weekly St. Andrew email"

    def handle(self, *args, **options):
        modules = [module for module in weekly_email()]
        content = [module.render() for module in modules]
        subjects = ["; ".join(module.subjects) for module in modules if module.subjects]
        subject = "; ".join(subjects)
        context = {"modules": content}

        html_message = render_to_string("emails/weekly_email.html", context)
        subject = "St. Andrew's Week Ahead: {}".format(subject)
        message = html2text(html_message)
        email_from = 'blocher@gmail.com'
        recipient_list = ['blocher@gmail.com', ]
        send_mail(subject, message, email_from, recipient_list, html_message=html_message)
