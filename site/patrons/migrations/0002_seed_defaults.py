from datetime import time

from django.db import migrations


def seed_defaults(apps, schema_editor):
    CalendarFeed = apps.get_model("patrons", "CalendarFeed")
    TextSchedule = apps.get_model("patrons", "TextSchedule")

    CalendarFeed.objects.get_or_create(name="Patrons Calendar", defaults={"enabled": True})
    for hour, minute, relative_days in [(17, 0, -1), (10, 30, 0), (20, 0, 0)]:
        TextSchedule.objects.get_or_create(time=time(hour=hour, minute=minute), relative_days=relative_days)


def remove_defaults(apps, schema_editor):
    CalendarFeed = apps.get_model("patrons", "CalendarFeed")
    TextSchedule = apps.get_model("patrons", "TextSchedule")

    CalendarFeed.objects.filter(name="Patrons Calendar").delete()
    for hour, minute, relative_days in [(17, 0, -1), (10, 30, 0), (20, 0, 0)]:
        TextSchedule.objects.filter(time=time(hour=hour, minute=minute), relative_days=relative_days).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("patrons", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_defaults, reverse_code=remove_defaults),
    ]
