# Generated by Django 5.1.4 on 2025-03-09 21:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("churchcal", "0013_commemoration_ai_bullet_points_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="commemoration",
            name="ai_image_1",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="commemoration",
            name="ai_image_2",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="commemoration",
            name="ai_legend_title",
            field=models.TextField(blank=True, null=True),
        ),
    ]
