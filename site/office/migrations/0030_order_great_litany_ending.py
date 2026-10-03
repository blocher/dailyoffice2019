from django.db import migrations
from django.db.models import F, Max


def forward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")
    database = schema_editor.connection.alias
    settings = Setting.objects.using(database).filter(site=1, setting_type=2)
    ending = settings.filter(name="great_litany_ending").first()
    litany_orders = list(
        settings.filter(name__in=("mp_great_litany", "ep_great_litany")).values_list("order", flat=True)
    )
    if ending and litany_orders:
        target_order = max(litany_orders) + 1
        settings.exclude(pk=ending.pk).filter(order__gte=target_order, order__lt=ending.order).update(
            order=F("order") + 1
        )
        ending.order = target_order
        ending.save(update_fields=["order"])

    SettingOption.objects.using(database).filter(setting=ending, value="litany").update(
        description=(
            "Omit the Supplication, retaining the concluding versicle and the collect beginning "
            "'Almighty God, you have promised.' When the Prayer of St. John Chrysostom is enabled, "
            "conclude with that prayer and the Grace; otherwise conclude with the Grace."
        )
    )


def backward(apps, schema_editor):
    Setting = apps.get_model("office", "Setting")
    SettingOption = apps.get_model("office", "SettingOption")
    database = schema_editor.connection.alias
    settings = Setting.objects.using(database).filter(site=1, setting_type=2)
    ending = settings.filter(name="great_litany_ending").first()
    if ending:
        previous_order = ending.order
        last_order = settings.exclude(pk=ending.pk).aggregate(value=Max("order"))["value"]
        settings.exclude(pk=ending.pk).filter(order__gt=previous_order).update(order=F("order") - 1)
        ending.order = 0 if last_order is None else last_order
        ending.save(update_fields=["order"])

    SettingOption.objects.using(database).filter(setting=ending, value="litany").update(
        description=(
            "Omit the Supplication, retaining the concluding versicle, the collect beginning "
            "'Almighty God, you have promised', and the Grace."
        )
    )


class Migration(migrations.Migration):
    dependencies = [("office", "0029_add_great_litany_ending")]

    operations = [migrations.RunPython(forward, backward)]
