from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from pymemcache.exceptions import MemcacheError

from churchcal import calculations


@override_settings(USE_CALENDAR_CACHE=True)
class CalendarCacheFailureTests(SimpleTestCase):
    def test_connection_reset_computes_the_calendar_without_retrying_cache(self):
        for error in (ConnectionResetError("reset"), TimeoutError("timeout"), MemcacheError("unavailable")):
            with self.subTest(error=type(error).__name__):
                calendar = Mock()
                with (
                    patch.object(calculations, "cache") as cache,
                    patch.object(calculations, "ChurchYear", return_value=calendar) as church_year,
                    patch("logging.Logger.warning") as warning,
                ):
                    cache.get.side_effect = error
                    self.assertIs(calculations.get_church_year("2026-10-05"), calendar)
                    church_year.assert_called_once_with(2025)
                    cache.set.assert_not_called()
                    warning.assert_called_once()

    def test_cache_hit_does_not_recompute_calendar(self):
        calendar = Mock()
        with patch.object(calculations, "cache") as cache, patch.object(calculations, "ChurchYear") as church_year:
            cache.get.return_value = calendar
            self.assertIs(calculations.get_church_year("2026-10-05"), calendar)
            cache.get.assert_called_once_with("2025")
            church_year.assert_not_called()
            cache.set.assert_not_called()

    def test_cache_miss_survives_failed_write(self):
        calendar = Mock()
        with (
            patch.object(calculations, "cache") as cache,
            patch.object(calculations, "ChurchYear", return_value=calendar),
            patch("logging.Logger.warning") as warning,
        ):
            cache.get.return_value = None
            cache.set.side_effect = ConnectionResetError("reset")
            self.assertIs(calculations.get_church_year("2026-10-05"), calendar)
            cache.set.assert_called_once_with("2025", calendar, 60 * 60 * 12)
            warning.assert_called_once()

    @override_settings(USE_CALENDAR_CACHE=False)
    def test_disabled_cache_is_neither_read_nor_written(self):
        with patch.object(calculations, "cache") as cache, patch.object(calculations, "ChurchYear") as church_year:
            self.assertIs(calculations.get_church_year("2026-10-05"), church_year.return_value)
            cache.get.assert_not_called()
            cache.set.assert_not_called()

    def test_calendar_calculation_errors_are_not_hidden(self):
        with patch.object(calculations, "cache") as cache, patch.object(calculations, "ChurchYear") as church_year:
            cache.get.return_value = None
            church_year.side_effect = ValueError("invalid calendar data")
            with self.assertRaisesMessage(ValueError, "invalid calendar data"):
                calculations.get_church_year("2026-10-05")
            cache.set.assert_not_called()
