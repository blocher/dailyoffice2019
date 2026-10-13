from django.db import migrations

# Settings titles shown in the app's Settings page. The end state is the
# same everywhere, though the starting titles have differed by environment.
TITLES = {
    "display_language": "Language",
    "language_style": "Language Style",
}

# A long-standing typo in a language style option (from migration 0009).
# Only the exact misspelling is corrected, so names edited since are kept.
TYPO = ("Contemporary Langauge", "Contemporary Language")


def forward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")
    for name, title in TITLES.items():
        Setting.objects.filter(name=name).update(title=title)
    SettingOption.objects.filter(setting__name="language_style", name=TYPO[0]).update(name=TYPO[1])


def backward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")
    Setting.objects.filter(name="display_language", title="Language").update(title="Display Language / 显示语言")
    SettingOption.objects.filter(setting__name="language_style", name=TYPO[1]).update(name=TYPO[0])


class Migration(migrations.Migration):
    dependencies = [("office", "0033_seed_alternate_readings")]
    operations = [migrations.RunPython(forward, backward)]
