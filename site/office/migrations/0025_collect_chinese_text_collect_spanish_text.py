from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0024_add_spanish_bible_and_language_setting"),
    ]

    operations = [
        migrations.AddField(
            model_name="collect",
            name="chinese_text",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="collect",
            name="spanish_text",
            field=models.TextField(blank=True, null=True),
        ),
    ]
