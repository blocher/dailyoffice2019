from django.db import migrations


def forward(apps, schema_editor):
    SettingOption = apps.get_model("office", "SettingOption")
    Setting = apps.get_model("office", "Setting")

    # Bible Translation
    bible_setting = Setting.objects.filter(name="bible_translation").first()
    if bible_setting:
        # Check if NVI exists
        if not SettingOption.objects.filter(setting=bible_setting, value="nvi").exists():
            SettingOption.objects.create(
                order=5,  # Assuming previous are 0,1,2,3,4.
                name="NVI",
                description="Nueva Versión Internacional",
                value="nvi",
                setting=bible_setting,
            )

    # Psalm Translation
    psalm_setting = Setting.objects.filter(name="psalm_translation").first()
    if psalm_setting:
        if not SettingOption.objects.filter(setting=psalm_setting, value="spanish").exists():
            SettingOption.objects.create(
                order=2,  # Assuming previous are 0,1
                name="Spanish (NVI)",
                description="Nueva Versión Internacional",
                value="spanish",
                setting=psalm_setting,
            )


def backward(apps, schema_editor):
    SettingOption = apps.get_model("office", "SettingOption")

    # Remove NVI Bible Translation
    SettingOption.objects.filter(value="nvi", setting__name="bible_translation").delete()

    # Remove Spanish Psalm Translation
    SettingOption.objects.filter(value="spanish", setting__name="psalm_translation").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0023_scripture_nvi"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
