from django.db import migrations, models


def forward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")

    # 1. Add Spanish Bible translation options to the existing bible_translation setting
    bible_translation = Setting.objects.get(name="bible_translation")

    SettingOption.objects.create(
        order=14,
        name="NVI (Nueva Versión Internacional)",
        description="Nueva Versión Internacional (1999)",
        value="nvi",
        setting=bible_translation,
        abbreviation="N",
    )

    SettingOption.objects.create(
        order=15,
        name="RVR1960 (Reina-Valera 1960)",
        description="Reina-Valera 1960",
        value="rv1960",
        setting=bible_translation,
        abbreviation="R",
    )

    # 2. Add Spanish option to the existing display_language setting
    display_language = Setting.objects.get(name="display_language")

    SettingOption.objects.create(
        order=3,
        name="Español",
        description="Mostrar contenido en español (Display content in Spanish)",
        value="spanish",
        setting=display_language,
        abbreviation="P",
    )


def backward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")

    # Remove Spanish bible translation options
    bible_translation = Setting.objects.get(name="bible_translation")
    SettingOption.objects.filter(
        setting=bible_translation,
        value__in=["nvi", "rv1960"],
    ).delete()

    # Remove Spanish display_language option
    display_language = Setting.objects.get(name="display_language")
    SettingOption.objects.filter(
        setting=display_language,
        value="spanish",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0023_add_chinese_bible_and_language_setting"),
    ]

    operations = [
        migrations.AddField(
            model_name="scripture",
            name="nvi",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scripture",
            name="rv1960",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(forward, backward),
    ]
