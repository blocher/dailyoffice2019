from django.db import migrations


def forward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")

    new_setting = Setting.objects.create(
        name="commemoration_info",
        title="Commemoration Info",
        description="",
        order=12,
        setting_type=2,
        site=1,
    )

    SettingOption.objects.create(
        order=0,
        name="Full Hagiography",
        description="Detailed biographies (from an orthodox Anglican perspective) featuring links to source materials, feast traditions, and commemoration ideas (compiled with AI assistance).",
        value="full_hagiography",
        setting=new_setting,
    )

    SettingOption.objects.create(
        order=1,
        name="Wikipedia link",
        description="A link to Wikipedia for the person being commemorated",
        value="wikipedia",
        setting=new_setting,
    )

    SettingOption.objects.create(
        order=2,
        name="Off",
        description="Hide the 'Learn More'button",
        value="off",
        setting=new_setting,
    )


def backward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    Setting.objects.filter(name="commemoration_info").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("office", "0020_setting_setting_string_order_and_more"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
