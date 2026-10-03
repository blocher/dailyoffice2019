from django.db import migrations
from django.db.models import Max


def forward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")
    database = schema_editor.connection.alias
    settings = Setting.objects.using(database)
    last_order = settings.filter(site=1, setting_type=2).aggregate(value=Max("order"))["value"]
    last_string_order = settings.aggregate(value=Max("setting_string_order"))["value"]
    setting = settings.create(
        name="great_litany_ending",
        title="Great Litany Ending",
        description=(
            "Choose the ending when the Great Litany is included in Morning or Evening Prayer. "
            "The Litany replaces the Prayer for Mission and concludes the Office."
        ),
        site=1,
        setting_type=2,
        order=0 if last_order is None else last_order + 1,
        setting_string_order=0 if last_string_order is None else last_string_order + 1,
    )
    options = [
        (
            "With the Supplication",
            "supplication",
            "S",
            "Include the Supplication. When the Prayer of St. John Chrysostom is enabled, "
            "conclude with that prayer and the Grace; otherwise end after the Supplication.",
        ),
        (
            "Short ending",
            "litany",
            "L",
            "Omit the Supplication, retaining the concluding versicle and the collect beginning "
            "'Almighty God, you have promised.' When the Prayer of St. John Chrysostom is enabled, "
            "conclude with that prayer and the Grace; otherwise conclude with the Grace.",
        ),
    ]
    for order, (name, value, abbreviation, description) in enumerate(options):
        SettingOption.objects.using(database).create(
            setting=setting,
            order=order,
            name=name,
            value=value,
            abbreviation=abbreviation,
            description=description,
        )


def backward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    Setting.objects.using(schema_editor.connection.alias).filter(name="great_litany_ending", site=1).delete()


class Migration(migrations.Migration):
    dependencies = [("office", "0028_merge_20260718_2138")]

    operations = [migrations.RunPython(forward, backward)]
