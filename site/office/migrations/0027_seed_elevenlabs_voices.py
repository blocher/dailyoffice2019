from django.db import migrations

# American premade voices that work well with eleven_v3.
# Leader roles are intentionally male-only (Brian).
# Note: ElevenLabs is retiring many "Default" voices on 2026-12-31; revisit
# these IDs in admin before then if your account loses access.
ELEVENLABS_VOICES = (
    # role, name, voice_id, order
    ("leader", "ElevenLabs Brian", "nPczCjzI2devNBz1zQrb", 0),  # American male, deep narration
    ("leader_dialogue", "ElevenLabs Brian", "nPczCjzI2devNBz1zQrb", 0),
    ("congregation", "ElevenLabs Sarah", "EXAVITQu4vr4xnSDxMaL", 0),  # American female, soft/clear
    ("congregation_dialogue", "ElevenLabs Sarah", "EXAVITQu4vr4xnSDxMaL", 0),
    ("reader", "ElevenLabs Bill", "pqHfZKP75CvOlQylNhV4", 0),  # American male, documentary narration
    ("reader", "ElevenLabs Adam", "pNInz6obpgDQGcFmaJgB", 1),  # American male, deep narration
    ("reader", "ElevenLabs Matilda", "XrExE9yKIg1WjnnlVkGX", 2),  # American female, friendly narration
)

SEEDED_VOICE_IDS = {voice_id for _, _, voice_id, _ in ELEVENLABS_VOICES}


def forward(apps, schema_editor):
    AudioVoice = apps.get_model("office", "AudioVoice")
    for role, name, voice_id, order in ELEVENLABS_VOICES:
        AudioVoice.objects.get_or_create(
            provider="elevenlabs",
            role=role,
            voice_id=voice_id,
            defaults={"name": name, "order": order, "enabled": True},
        )


def backward(apps, schema_editor):
    AudioVoice = apps.get_model("office", "AudioVoice")
    AudioVoice.objects.filter(provider="elevenlabs", voice_id__in=SEEDED_VOICE_IDS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0026_audiogenerationconfig_audiocostrate_and_more"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
