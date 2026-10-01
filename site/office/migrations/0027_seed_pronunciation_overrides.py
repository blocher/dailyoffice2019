from django.db import migrations

DEFAULTS = [
    {"match": "LORD", "replacement": "Lord", "is_regex": False, "order": 10, "note": "Small-caps LORD -> Lord"},
    {
        "match": "Lᴏʀᴅ",
        "replacement": "Lord",
        "is_regex": False,
        "order": 11,
        "note": "Unicode small-caps LORD -> Lord",
    },
    {
        "match": "Amen",
        "replacement": "Ah-men",
        "is_regex": False,
        "order": 20,
        "note": "Fix 'AY-men' mispronunciation",
    },
    {
        "match": "Christ, have mercy",
        "replacement": "Christ have mercy",
        "is_regex": False,
        "order": 30,
        "note": "Comma caused 'Christ' to be dropped in the Kyrie",
    },
]


def seed(apps, schema_editor):
    PronunciationOverride = apps.get_model("office", "PronunciationOverride")
    for entry in DEFAULTS:
        PronunciationOverride.objects.get_or_create(
            match=entry["match"],
            replacement=entry["replacement"],
            defaults={
                "is_regex": entry["is_regex"],
                "order": entry["order"],
                "enabled": True,
                "note": entry["note"],
            },
        )


def unseed(apps, schema_editor):
    PronunciationOverride = apps.get_model("office", "PronunciationOverride")
    for entry in DEFAULTS:
        PronunciationOverride.objects.filter(match=entry["match"], replacement=entry["replacement"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("office", "0026_audioclip_pronunciationoverride"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
