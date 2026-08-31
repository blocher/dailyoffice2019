from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("office", "0028_merge_20260718_2138"),
    ]

    operations = [
        migrations.AlterField(
            model_name="audioclip",
            name="text",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Normalized text sent to the TTS provider.",
            ),
        ),
        migrations.AddField(
            model_name="audioclip",
            name="word_timing",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Provider word alignment relative to the beginning of this clip.",
            ),
        ),
        migrations.AddField(
            model_name="audioclip",
            name="provider",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=32,
            ),
        ),
    ]
