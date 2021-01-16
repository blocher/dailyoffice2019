import html2text
# from django.core.mail import send_mail
#
#
#
# def send_st_andrew_email():
#
#     subject = 'Test Email'
#     message = ' it  means a world to us '
#     email_from = 'blocher@gmail.com'
#     recipient_list = ['blocher@gmail.com', ]
#     send_mail(subject, message, email_from, recipient_list)

from mailgun2 import Mailgun

from website.settings import (
    DEFAULT_FROM_EMAIL,
    DEFAULT_REPLY_TO_EMAIL,
    MAILGUN_DOMAIN,
    MAILGUN_PUBLIC_KEY,
    MAILGUN_PRIVATE_KEY,
)


def send_mail(
    subject,
    message=None,
    from_email=None,
    recipient_list=[],
    to=[],
    text=None,
    html=None,
    cc=None,
    bcc=None,
    tags=None,
    reply_to=None,
    headers=None,
    inlines=None,
    attachments=None,
):
    mailer = Mailgun(MAILGUN_DOMAIN, MAILGUN_PUBLIC_KEY, MAILGUN_PRIVATE_KEY)
    params = {
        "from_email": from_email or DEFAULT_FROM_EMAIL,
        "to": recipient_list or to,
        "subject": subject,
        "text": text or html2text.html2text(message) if message else "",
        "html": html or message,
        "cc": cc,
        "bcc": bcc,
        "tags": tags,
        "reply_to": reply_to or DEFAULT_REPLY_TO_EMAIL,
        "headers": headers,
        "inlines": inlines,
        "attachments": attachments,
    }
    return mailer.send_message(**params)
