from django.db import migrations, models


def limit_amen_override_to_openai(apps, schema_editor):
    PronunciationOverride = apps.get_model("office", "PronunciationOverride")
    PronunciationOverride.objects.filter(match="Amen", replacement="Ah-men").update(providers="openai")


def restore_amen_override(apps, schema_editor):
    PronunciationOverride = apps.get_model("office", "PronunciationOverride")
    PronunciationOverride.objects.filter(match="Amen", replacement="Ah-men").update(providers="")


class Migration(migrations.Migration):

    dependencies = [
        ("office", "0029_audioclip_word_timing"),
    ]

    operations = [
        migrations.AddField(
            model_name="pronunciationoverride",
            name="providers",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Comma-separated TTS providers this rule applies to (e.g. openai). Leave blank for all.",
                max_length=128,
            ),
        ),
        migrations.RunPython(limit_amen_override_to_openai, restore_amen_override),
    ]
