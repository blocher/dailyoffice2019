import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.http import QueryDict
from django.test import SimpleTestCase

from office.api.views.index import ReadingModule, Settings


class QuerySettingsTests(SimpleTestCase):
    options = {
        "reading_cycle": ["1", "2"],
        "psalter": ["30", "60"],
        "canticle_rotation": ["default", "2011"],
        "reading_length": ["full", "abbreviated"],
        "lectionary": ["daily-office-readings", "mass-readings"],
    }

    def settings(self, query):
        request = SimpleNamespace(query_params=QueryDict(query))
        with patch.object(Settings, "_setting_options", return_value=self.options):
            return Settings(request)

    def test_comma_joined_settings_produce_a_valid_reading(self):
        settings = self.settings("reading_cycle=1,1&psalter=30,30&canticle_rotation=default,2011")
        self.assertEqual(settings["reading_cycle"], "1")
        self.assertEqual(settings["psalter"], "30")
        self.assertEqual(settings["canticle_rotation"], "2011")
        module = object.__new__(ReadingModule)
        module.office = SimpleNamespace(settings=settings, date=SimpleNamespace(date=datetime.date(2026, 10, 5)))
        with (
            patch.object(ReadingModule, "bible_translation", "esv"),
            patch.object(module, "get_reading", return_value=["reading"]) as reading,
        ):
            self.assertEqual(module.get_lines_for_reading("mp", 1), ["reading"])
        reading.assert_called_once_with("mp_reading_1", False, "esv")

    def test_last_supported_option_wins_and_invalid_values_keep_defaults(self):
        settings = self.settings("reading_cycle=1,2,unknown&psalter=invalid&reading_length=&unknown=2")
        self.assertEqual(settings["reading_cycle"], "2")
        self.assertEqual(settings["psalter"], "30")
        self.assertEqual(settings["reading_length"], "full")
        self.assertNotIn("unknown", settings)

    def test_scalar_and_repeated_query_parameters_keep_last_value(self):
        settings = self.settings("reading_cycle=1&reading_cycle=2&psalter=60")
        self.assertEqual(settings["reading_cycle"], "2")
        self.assertEqual(settings["psalter"], "60")

    def test_declared_option_containing_commas_is_preserved(self):
        with patch.dict(self.options, {"custom": ["default", "one,two"]}):
            self.assertEqual(self.settings("custom=one,two")["custom"], "one,two")

    def test_options_and_defaults_come_from_the_same_ordered_query(self):
        rows = [
            SimpleNamespace(name="reading_cycle", options=[SimpleNamespace(value="1"), SimpleNamespace(value="2")])
        ]
        with patch("office.api.views.index.Setting.objects") as manager:
            manager.order_by.return_value.prefetch_related.return_value.all.return_value = rows
            settings = Settings(SimpleNamespace(query_params=QueryDict("reading_cycle=2")))
        self.assertEqual(settings["reading_cycle"], "2")
        manager.order_by.assert_called_once_with("site", "setting_type", "order")
