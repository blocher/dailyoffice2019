from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.utils import timezone

from patrons.dates import EASTERN_TIME, is_schedule_due, relative_day_phrase
from patrons.models import Event, PatronalFeast, TextMessageSend, TextRecipient, TextSchedule

try:
    from twilio.rest import Client
except ImportError:
    Client = None


def format_patronal_feast_message(feast, occurrence_date, today):
    days_until = (occurrence_date - today).days
    calendar_text = feast.calendar_label_text_for_date(occurrence_date)
    suffix = " {}".format(calendar_text) if calendar_text else ""
    return "{} is celebrating a patronal feast {} for {}: {}.{}".format(
        feast.family_member.first_name,
        relative_day_phrase(days_until),
        feast.normalized_name,
        feast.display_feast_name,
        suffix,
    )


def format_event_message(event, occurrence_date, today):
    days_until = (occurrence_date - today).days
    return "{} has a {} anniversary {}.".format(
        event.family_member.first_name,
        event.get_event_type_display(),
        relative_day_phrase(days_until),
    )


def send_sms(to_number, message):
    if Client is None:
        raise ImproperlyConfigured("The twilio package is not installed.")
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", "")
    if not account_sid or not auth_token or not from_number:
        raise ImproperlyConfigured("Twilio settings are missing.")

    client = Client(account_sid, auth_token)
    twilio_message = client.messages.create(body=message, from_=from_number, to=to_number)
    return twilio_message.sid


def due_schedules(now):
    return [schedule for schedule in TextSchedule.objects.all() if is_schedule_due(now, schedule.time)]


def due_patronal_feasts(target_date):
    return [
        feast
        for feast in PatronalFeast.objects.select_related("family_member").all()
        if feast.matches_date(target_date)
    ]


def due_events(target_date):
    return [event for event in Event.objects.select_related("family_member").all() if event.matches_date(target_date)]


def create_send_log(recipient, schedule, occurrence_date, message, event=None, patronal_feast=None):
    try:
        with transaction.atomic():
            return TextMessageSend.objects.create(
                recipient=recipient,
                schedule=schedule,
                event=event,
                patronal_feast=patronal_feast,
                occurrence_date=occurrence_date,
                message=message,
            )
    except IntegrityError:
        return None


def send_due_reminders(now=None, dry_run=False):
    now = now or timezone.now()
    local_today = now.astimezone(EASTERN_TIME).date()
    schedules = due_schedules(now)
    if not schedules:
        return 0
    if not getattr(settings, "PATRONS_SMS_ENABLED", False) and not dry_run:
        return 0

    recipients = list(TextRecipient.objects.filter(enabled=True).select_related("family_member"))
    sent_count = 0
    for schedule in schedules:
        occurrence_date = local_today - timedelta(days=schedule.relative_days)
        events = due_events(occurrence_date)
        feasts = due_patronal_feasts(occurrence_date)

        for recipient in recipients:
            for event in events:
                message = format_event_message(event, occurrence_date, local_today)
                if dry_run:
                    sent_count += 1
                    continue
                send_log = create_send_log(recipient, schedule, occurrence_date, message, event=event)
                if send_log is None:
                    continue
                try:
                    send_log.provider_message_id = send_sms(recipient.telephone_number, message)
                    send_log.success = True
                except Exception as exc:
                    send_log.error_message = str(exc)
                send_log.save(update_fields=["provider_message_id", "success", "error_message", "updated"])
                sent_count += 1

            for feast in feasts:
                message = format_patronal_feast_message(feast, occurrence_date, local_today)
                if dry_run:
                    sent_count += 1
                    continue
                send_log = create_send_log(
                    recipient,
                    schedule,
                    occurrence_date,
                    message,
                    patronal_feast=feast,
                )
                if send_log is None:
                    continue
                try:
                    send_log.provider_message_id = send_sms(recipient.telephone_number, message)
                    send_log.success = True
                except Exception as exc:
                    send_log.error_message = str(exc)
                send_log.save(update_fields=["provider_message_id", "success", "error_message", "updated"])
                sent_count += 1

    return sent_count
