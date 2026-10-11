import datetime
import os
import tempfile
import time
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from office.management.commands.cleanup_full_audio_files import Command as CleanupFullAudioCommand
from office.models import Scripture
from office.api.views.index import (
    Dismissal,
    EPAdditionalCollects,
    EPGreatLitany,
    EveningPrayer,
    FinalPrayers,
    FamilyMorningCollect,
    FamilyEarlyEveningCollect,
    FamilyCloseOfDayCollect,
    GreatLitanyAloneModule,
    Intercessions,
    MPAdditionalCollects,
    MPGreatLitany,
    MorningPrayer,
    Prayers,
    Settings,
)


class NormalizeBibleTranslationTests(TestCase):
    def test_undefined_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("undefined"), "esv")

    def test_null_and_none_strings_default_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("null"), "esv")
        self.assertEqual(Scripture.normalize_bible_translation("none"), "esv")

    def test_empty_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation(""), "esv")
        self.assertEqual(Scripture.normalize_bible_translation(None), "esv")

    def test_valid_translation_is_normalized(self):
        self.assertEqual(Scripture.normalize_bible_translation("NRSVCE"), "nrsvce")

    def test_unknown_translation_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("msg"), "esv")


class CleanupFullAudioFilesTests(TestCase):
    def test_scan_dirs_includes_provider_subfolders(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "openai_v2"))
            os.makedirs(os.path.join(tmp, "fish"))
            dirs = CleanupFullAudioCommand()._scan_dirs(tmp)
            self.assertEqual(
                dirs,
                [tmp, os.path.join(tmp, "fish"), os.path.join(tmp, "openai_v2")],
            )

    @override_settings(MEDIA_ROOT="")
    def test_deletes_ffmpeg_full_tracks_in_openai_v2(self):
        with tempfile.TemporaryDirectory() as tmp:
            v2 = os.path.join(tmp, "openai_v2")
            os.makedirs(v2)
            full_path = os.path.join(v2, "full-track.mp3")
            clip_path = os.path.join(v2, "clip.mp3")
            for path in (full_path, clip_path):
                with open(path, "wb") as f:
                    f.write(b"fake-mp3")
                # Older than --days 7
                old = time.time() - (8 * 86400)
                os.utime(path, (old, old))

            def fake_mp3(path):
                audio = MagicMock()
                if path.endswith("full-track.mp3"):
                    tag = MagicMock()
                    tag.text = ["Lavf61.7.100"]
                    audio.tags.getall.return_value = [tag]
                else:
                    audio.tags = None
                return audio

            with (
                override_settings(MEDIA_ROOT=tmp),
                patch(
                    "office.management.commands.cleanup_full_audio_files.MP3",
                    side_effect=fake_mp3,
                ),
            ):
                out = StringIO()
                call_command("cleanup_full_audio_files", "--execute", "--days", "7", stdout=out)

            self.assertFalse(os.path.exists(full_path))
            self.assertTrue(os.path.exists(clip_path))
            self.assertIn("openai_v2/full-track.mp3", out.getvalue())


class EmbeddedGreatLitanyTests(SimpleTestCase):
    office_classes = (
        (MorningPrayer, MPAdditionalCollects, MPGreatLitany, "mp"),
        (EveningPrayer, EPAdditionalCollects, EPGreatLitany, "ep"),
    )

    def make_office(self, weekday=0, **settings):
        defaults = {
            "mp_great_litany": "mp_litany_off",
            "ep_great_litany": "ep_litany_off",
            "language_style": "contemporary",
            "language_style_for_our_father": "contemporary",
            "national_holidays": "us",
            "suffrages": "a",
            "collects": "weekly",
            "extra_collects": [],
            "general_thanksgiving": "on",
            "chrysostom": "on",
            "grace": "rotating",
        }
        defaults.update(settings)
        return SimpleNamespace(
            settings=defaults,
            date=SimpleNamespace(
                date=datetime.date(2026, 9, 28) + datetime.timedelta(days=weekday),
                all=[],
                all_evening=[],
                season=SimpleNamespace(name="Season After Pentecost"),
            ),
        )

    @staticmethod
    def content(lines):
        return "\n".join(line["content"].strip() for line in lines or [])

    @staticmethod
    def collect(title):
        return {"title": title, "contemporary": f"{title} text", "traditional": f"{title} traditional text"}

    def test_litany_schedule_controls_mission_and_office_conclusion_together(self):
        for office_class, collects_class, litany_class, prefix in self.office_classes:
            for schedule in ("off", "everyday", "w_f_s"):
                for weekday in range(7):
                    active = schedule == "everyday" or (schedule == "w_f_s" and weekday in (2, 4, 6))
                    for rotation in ("weekly", "fixed"):
                        for style in ("contemporary", "traditional"):
                            with self.subTest(
                                office=prefix, schedule=schedule, weekday=weekday, rotation=rotation, style=style
                            ):
                                office = self.make_office(
                                    weekday,
                                    **{
                                        f"{prefix}_great_litany": f"{prefix}_litany_{schedule}",
                                        "collects": rotation,
                                        "language_style": style,
                                    },
                                )
                                modules = office_class.get_modules(office)
                                self.assertEqual(isinstance(modules[-1], litany_class), active)
                                for tail_class in (Intercessions, FinalPrayers, Dismissal):
                                    self.assertEqual(
                                        any(isinstance(module, tail_class) for module in modules), not active
                                    )
                                collects = next(module for module in modules if isinstance(module, collects_class))
                                with (
                                    patch.object(collects, "pick_weekly_collect", return_value=self.collect("Weekly")),
                                    patch.object(
                                        collects, "pick_fixed_collects", return_value=(self.collect("Fixed"),)
                                    ),
                                    patch.object(
                                        collects, "get_extra_collects", return_value=(self.collect("Extra"),)
                                    ),
                                    patch.object(
                                        collects,
                                        "pick_mission_collect",
                                        return_value=self.collect("A Prayer for Mission"),
                                    ) as mission,
                                ):
                                    text = self.content(collects.get_lines())
                                self.assertEqual("A Prayer for Mission" in text, not active)
                                self.assertEqual(mission.call_count, int(not active))
                                self.assertIn("Extra", text)
                                self.assertIn("Weekly" if rotation == "weekly" else "Fixed", text)
                                self.assertEqual(bool(litany_class(office).get_lines()), active)

    def test_morning_and_evening_schedules_are_independent(self):
        for active_prefix in ("mp", "ep"):
            office = self.make_office(**{f"{active_prefix}_great_litany": f"{active_prefix}_litany_everyday"})
            for office_class, _, litany_class, prefix in self.office_classes:
                with self.subTest(active=active_prefix, office=prefix):
                    self.assertEqual(
                        isinstance(office_class.get_modules(office)[-1], litany_class), prefix == active_prefix
                    )

    def test_short_ending_retains_versicle_collect_chrysostom_and_grace_without_supplication(self):
        for _, _, litany_class, prefix in self.office_classes:
            for style in ("contemporary", "traditional"):
                with self.subTest(office=prefix, style=style):
                    office = self.make_office(
                        **{
                            f"{prefix}_great_litany": f"{prefix}_litany_everyday",
                            "great_litany_ending": "litany",
                            "language_style": style,
                        }
                    )
                    module = litany_class(office)
                    lines = module.get_formatted_lines()
                    text = self.content(lines)
                    self.assertNotIn("The Supplication", text)
                    self.assertNotIn("Look mercifully", text)
                    self.assertIn("O Lord, show us", text)
                    collect = (
                        "Almighty God, who hast promised"
                        if style == "traditional"
                        else "Almighty God, you have promised"
                    )
                    self.assertIn(collect, text)
                    self.assertEqual(text.count("given us grace at this time"), 1)
                    self.assertEqual(text.count("The grace of our Lord Jesus Christ"), 1)
                    self.assertLess(text.index("O Lord, show us"), text.index(collect))
                    self.assertLess(text.index(collect), text.index("given us grace at this time"))
                    self.assertLess(
                        text.index("given us grace at this time"), text.index("The grace of our Lord Jesus Christ")
                    )
                    self.assertNotIn("Let us bless the Lord.", text)
                    collect_line = next(line for line in lines if line["content"].startswith(collect))
                    self.assertFalse(collect_line["content"].endswith("Amen."))
                    self.assertTrue(all("id" in line and "audio_id" in line for line in lines))

    def test_supplication_remains_default_and_replaces_short_ending_collect(self):
        for _, _, litany_class, prefix in self.office_classes:
            for style in ("contemporary", "traditional"):
                for explicit_setting in ({}, {"great_litany_ending": "supplication"}):
                    with self.subTest(office=prefix, style=style, explicit=explicit_setting):
                        office = self.make_office(
                            **{
                                f"{prefix}_great_litany": f"{prefix}_litany_everyday",
                                "language_style": style,
                                **explicit_setting,
                            }
                        )
                        text = self.content(litany_class(office).get_lines())
                        self.assertIn("The Supplication", text)
                        self.assertIn("Look mercifully", text)
                        self.assertNotIn("Almighty God, you have promised", text)
                        self.assertNotIn("Almighty God, who hast promised", text)
                        self.assertEqual(text.count("The grace of our Lord Jesus Christ"), 1)
                        self.assertIn("given us grace at this time", text)

    def test_supplication_can_end_without_optional_chrysostom_and_grace(self):
        for _, _, litany_class, prefix in self.office_classes:
            for style in ("contemporary", "traditional"):
                with self.subTest(office=prefix, style=style):
                    office = self.make_office(
                        **{
                            f"{prefix}_great_litany": f"{prefix}_litany_everyday",
                            "language_style": style,
                            "chrysostom": "off",
                        }
                    )
                    text = self.content(litany_class(office).get_lines())
                    self.assertIn("Look mercifully", text)
                    self.assertNotIn("given us grace at this time", text)
                    self.assertNotIn("The grace of our Lord Jesus Christ", text)

    def test_short_ending_omits_chrysostom_when_setting_is_off(self):
        for _, _, litany_class, prefix in self.office_classes:
            for style in ("contemporary", "traditional"):
                with self.subTest(office=prefix, style=style):
                    office = self.make_office(
                        **{
                            f"{prefix}_great_litany": f"{prefix}_litany_everyday",
                            "great_litany_ending": "litany",
                            "language_style": style,
                            "chrysostom": "off",
                        }
                    )
                    text = self.content(litany_class(office).get_lines())
                    self.assertNotIn("given us grace at this time", text)
                    self.assertEqual(text.count("The grace of our Lord Jesus Christ"), 1)

    def test_lords_prayer_remains_in_both_office_and_litany(self):
        for _, _, litany_class, prefix in self.office_classes:
            for style in ("contemporary", "traditional"):
                for ending in ("litany", "supplication"):
                    with self.subTest(office=prefix, style=style, ending=ending):
                        office = self.make_office(
                            **{
                                f"{prefix}_great_litany": f"{prefix}_litany_everyday",
                                "language_style": style,
                                "great_litany_ending": ending,
                            }
                        )
                        office_prayers = self.content(Prayers(office).get_lines())
                        litany_prayers = self.content(litany_class(office).get_lines())
                        self.assertEqual(office_prayers.count("Our Father"), 1)
                        self.assertEqual(litany_prayers.count("Our Father"), 1)
                        self.assertIn("Lord, have mercy", litany_prayers)

    def test_short_ending_uses_available_spanish_text(self):
        office = self.make_office(
            mp_great_litany="mp_litany_everyday", great_litany_ending="litany", display_language="spanish"
        )
        text = self.content(MPGreatLitany(office).get_formatted_lines())
        self.assertIn("Dios Todopoderoso, que has prometido", text)
        self.assertIn("La gracia de nuestro Señor Jesucristo", text)
        self.assertNotIn("Almighty God, you have promised", text)

    def test_litany_retains_commemorations_and_leader_substitutions(self):
        office = self.make_office(mp_great_litany="mp_litany_everyday", great_litany_ending="litany")
        office.date.all = [SimpleNamespace(saint_name="Test Saint")]
        text = self.content(MPGreatLitany(office).get_lines())
        self.assertIn("the Blessed Virgin Mary, Test Saint and", text)
        self.assertNotIn("[_____________ and]", text)
        self.assertNotIn("{{ leaders }}", text)
        self.assertIn("President of the United States", text)

    def test_standalone_litany_forms_remain_available(self):
        for style in ("contemporary", "traditional"):
            for portion in ("both", "litany", "supplication"):
                with self.subTest(style=style, portion=portion):
                    text = self.content(GreatLitanyAloneModule(style, portion).get_formatted_lines())
                    self.assertEqual("The Supplication" in text, portion in ("both", "supplication"))
                    self.assertEqual("O Lamb of God" in text, portion in ("both", "litany"))
                    self.assertEqual("Our Father" in text, portion in ("both", "litany"))
                    self.assertIn("The grace of our Lord Jesus Christ", text)

    def test_ending_option_is_accepted_by_api_settings(self):
        request = SimpleNamespace(query_params={"great_litany_ending": "litany"})
        with patch.object(
            Settings, "_setting_options", return_value={"great_litany_ending": ["supplication", "litany"]}
        ):
            self.assertEqual(Settings(request)["great_litany_ending"], "litany")

    def test_family_collects_do_not_change_when_daily_office_litany_is_enabled(self):
        family_collects = (
            (FamilyMorningCollect, MPAdditionalCollects),
            (FamilyEarlyEveningCollect, EPAdditionalCollects),
            (FamilyCloseOfDayCollect, EPAdditionalCollects),
        )
        for family_class, collects_class in family_collects:
            for style in ("contemporary", "traditional"):
                with self.subTest(family=family_class.__name__, style=style):
                    texts = []
                    for schedule in ("off", "everyday"):
                        office = self.make_office(
                            mp_great_litany=f"mp_litany_{schedule}",
                            ep_great_litany=f"ep_litany_{schedule}",
                            language_style=style,
                            family_collect="day_of_week",
                        )
                        with (
                            patch.object(collects_class, "pick_weekly_collect", return_value=self.collect("Weekly")),
                            patch.object(collects_class, "get_extra_collects", return_value=(self.collect("Extra"),)),
                            patch.object(
                                collects_class,
                                "pick_mission_collect",
                                return_value=self.collect("A Prayer for Mission"),
                            ),
                        ):
                            texts.append(self.content(family_class(office).get_lines()))
                    self.assertEqual(texts[0], texts[1])
                    self.assertIn("A Prayer for Mission", texts[1])
                    self.assertIn("Extra", texts[1])
