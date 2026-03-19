from django.db import migrations


def forward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")

    # 1. Add Chinese Bible translation options to the existing bible_translation setting
    bible_translation = Setting.objects.get(name="bible_translation")

    SettingOption.objects.create(
        order=10,
        name="CUV (繁體)",
        description="和合本 (繁體) Chinese Union Version, Traditional (1919)",
        value="cuv",
        setting=bible_translation,
        abbreviation="C",
    )

    SettingOption.objects.create(
        order=11,
        name="CUVS (简体)",
        description="和合本 (简体) Chinese Union Version, Simplified (1919)",
        value="cuvs",
        setting=bible_translation,
        abbreviation="S",
    )

    SettingOption.objects.create(
        order=12,
        name="思高本 (繁體)",
        description="思高聖經 Sigao Bible, Traditional Chinese Catholic translation",
        value="sigao",
        setting=bible_translation,
        abbreviation="G",
    )

    SettingOption.objects.create(
        order=13,
        name="思高本 (简体)",
        description="思高圣经 Sigao Bible, Simplified Chinese Catholic translation",
        value="znsigao",
        setting=bible_translation,
        abbreviation="Z",
    )

    # 2. Create a display_language setting
    # Shift existing main settings (setting_type=1) to make room at order=0
    main_settings = Setting.objects.filter(setting_type=1, site=1).all()
    for setting in main_settings:
        setting.order = setting.order + 1
        setting.save()

    new_setting = Setting.objects.create(
        name="display_language",
        title="Display Language / 显示语言",
        description="The language for prayers, headings, and other liturgical text",
        order=0,
        setting_type=1,
        site=1,
    )

    SettingOption.objects.create(
        order=0,
        name="English",
        description="Display all content in English",
        value="english",
        setting=new_setting,
        abbreviation="E",
    )

    SettingOption.objects.create(
        order=1,
        name="繁體中文",
        description="以繁體中文顯示內容 (Display content in Traditional Chinese)",
        value="chinese-traditional",
        setting=new_setting,
        abbreviation="T",
    )

    SettingOption.objects.create(
        order=2,
        name="简体中文",
        description="以简体中文显示内容 (Display content in Simplified Chinese)",
        value="chinese-simplified",
        setting=new_setting,
        abbreviation="S",
    )


def backward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")

    # Remove Chinese bible translation options
    bible_translation = Setting.objects.get(name="bible_translation")
    SettingOption.objects.filter(
        setting=bible_translation,
        value__in=["cuv", "cuvs", "sigao", "znsigao"],
    ).delete()

    # Remove display_language setting (cascades to options)
    Setting.objects.filter(name="display_language").delete()

    # Shift main settings back
    main_settings = Setting.objects.filter(setting_type=1, site=1).all()
    for setting in main_settings:
        setting.order = setting.order - 1
        setting.save()


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0022_scripture_cuv_scripture_cuvs_scripture_sigao_scripture_znsigao"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
