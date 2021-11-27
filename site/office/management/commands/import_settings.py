from django.core.management.base import BaseCommand

from office.context_processors import (
    settings_dict,
    minor_settings_dict,
    family_settings_dict,
    family_minor_settings_dict,
)

from office.models import Setting, SettingOption


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_setting(self, setting_data, order=0, setting_type=Setting.MAIN_SETTINGS, site=Setting.DAILY_OFFICE_SITE):
        setting = Setting.objects.get_or_create(name=setting_data["name"], setting_type=setting_type, site=site)[0]
        setting.title = setting_data["title"]
        setting.description = setting_data["help_text"]
        setting.order = order
        setting.save()

        for order, option_data in enumerate(setting_data["options"]):
            option = SettingOption.objects.get_or_create(setting=setting, value=option_data["value"])[0]
            option.name = option_data["heading"]
            try:
                option.description = option_data["text"]
            except KeyError:
                option.description = option_data["value"]
            option.order = order
            option.save()

    def handle(self, *args, **options):
        Setting.objects.all().delete()
        SettingOption.objects.all().delete()
        settings = {
            "settings": settings_dict,
            "minor_settings": minor_settings_dict,
            "family_settings": family_settings_dict,
            "family_minor_settings": family_minor_settings_dict,
        }
        for order, setting in enumerate(settings["settings"]):
            self.add_setting(setting, order)
        for order, setting in enumerate(settings["minor_settings"]):
            self.add_setting(setting, order, setting_type=Setting.ADDITIONAL_SETTINGS)
        for order, setting in enumerate(settings["family_settings"]):
            self.add_setting(setting, order, site=Setting.FAMILY_PRAYER_SITE)
        for order, setting in enumerate(settings["family_minor_settings"]):
            self.add_setting(setting, order, site=Setting.FAMILY_PRAYER_SITE, setting_type=Setting.ADDITIONAL_SETTINGS)
