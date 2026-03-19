from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("psalter", "0005_psalmverse_first_half_tle_psalmverse_second_half_tle"),
    ]

    operations = [
        migrations.AddField(
            model_name="psalmverse",
            name="first_half_spanish",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name="psalmverse",
            name="second_half_spanish",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
