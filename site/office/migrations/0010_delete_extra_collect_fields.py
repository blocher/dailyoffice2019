# Generated by Django 4.0.4 on 2022-08-01 01:30
from django.core.management import call_command
from django.db import migrations


def forward(apps, schema_editor):
    call_command("import_collects")


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0009_add_trad_language_setting"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]