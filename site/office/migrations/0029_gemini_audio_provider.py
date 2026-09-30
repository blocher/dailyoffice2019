from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("office", "0028_audiousage_request_path_textfield")]

    operations = [
        migrations.AlterField(
            model_name="audiogenerationconfig",
            name="provider_mode",
            field=models.CharField(
                choices=[
                    ("openai", "OpenAI"),
                    ("gemini", "Gemini TTS"),
                    ("elevenlabs_v3", "ElevenLabs v3"),
                    ("elevenlabs_studio", "ElevenLabs Studio"),
                ],
                default="openai",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="audiovoice",
            name="provider",
            field=models.CharField(
                choices=[("openai", "OpenAI"), ("gemini", "Gemini TTS"), ("elevenlabs", "ElevenLabs")], max_length=32
            ),
        ),
        migrations.AlterField(
            model_name="audiogeneratedfile",
            name="provider",
            field=models.CharField(
                choices=[
                    ("openai", "OpenAI"),
                    ("gemini", "Gemini TTS"),
                    ("elevenlabs", "ElevenLabs"),
                    ("local", "Local"),
                ],
                max_length=32,
            ),
        ),
    ]
