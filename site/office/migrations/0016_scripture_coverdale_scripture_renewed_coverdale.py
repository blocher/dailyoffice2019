# Generated by Django 4.0.4 on 2022-10-10 02:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0015_lectionaryitem_sanctorale_commemoration"),
    ]

    operations = [
        migrations.AddField(
            model_name="scripture",
            name="coverdale",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scripture",
            name="renewed_coverdale",
            field=models.TextField(blank=True, null=True),
        ),
    ]
