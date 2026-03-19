from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("psalter", "0006_psalmverse_spanish_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="psalmverse",
            name="first_half_chinese",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name="psalmverse",
            name="second_half_chinese",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
