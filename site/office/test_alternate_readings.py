import datetime
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from office.alternate_readings import alternate_first_lesson
from office.api.views.index import (
    ReadingModule,
    Settings,
    office_lesson_formats,
    SETTING_UI_METADATA,
    GenericDailyOfficeSerializer,
)
from office.migrations._alternate_readings_0033 import (
    forward,
    backward,
    extract,
    plan,
    scripture_texts,
    body_text,
)
from office.models import AlternateReading, Scripture, StandardOfficeDay


def marked(verses, chapter=3, language="English", book="Exod"):
    return '<div><h3><span class="text %s-%s-%s">Heading</span></h3><p>%s</p></div>' % (
        book,
        chapter,
        verses[0],
        " ".join(
            f'<span class="text {book}-{chapter}-{v}"><sup class="versenum">{v}</sup>{language} verse {v}.</span>'
            for v in verses
        ),
    )


def appointed_day(model=StandardOfficeDay, **overrides):
    values = dict(
        mp_psalms="1",
        ep_psalms="2",
        mp_reading_1="Exodus 3",
        mp_reading_1_testament="OT",
        ep_reading_1="Baruch 4",
        ep_reading_1_testament="AP",
        mp_reading_2="John 1",
        mp_reading_2_testament="NT",
        ep_reading_2="Romans 1",
        ep_reading_2_testament="NT",
    )
    if model.__name__ == "StandardOfficeDay":
        values.update(month=2, day=23)
    values.update(overrides)
    return model.objects.create(**values)


class AlternateReadingTests(TestCase):
    def setUp(self):
        self.day = appointed_day()
        self.whole = Scripture.objects.create(
            passage="Exodus 3", esv=marked(list(range(1, 23))), nrsvce=marked(list(range(1, 23)), language="Fallback")
        )
        self.morning = Scripture.objects.create(
            passage="Exodus 3:1-12",
            esv=marked(list(range(1, 13))),
            nrsvce=marked(list(range(1, 13)), language="Fallback"),
        )
        self.evening = Scripture.objects.create(
            passage="Exodus 3:13-22",
            esv=marked(list(range(13, 23))),
            nrsvce=marked(list(range(13, 23)), language="Fallback"),
        )
        self.mapping = AlternateReading.objects.create(
            office_day=self.day, donor_office="mp", whole=self.whole, morning=self.morning, evening=self.evening
        )
        Scripture.objects.create(
            passage="Baruch 4", esv="<p>Appointed Apocrypha</p>", nrsvce="<p>Appointed Apocrypha</p>"
        )
        Scripture.objects.create(passage="John 1", esv="<p>Morning second</p>")
        Scripture.objects.create(passage="Romans 1", esv="<p>Evening second</p>")
        self.settings = dict(
            apocrypha_readings="alternate",
            reading_cycle="1",
            reading_length="full",
            lectionary="daily-office-readings",
            reading_headings="on",
            reading_audio="on",
            bible_translation="esv",
            display_language="english",
        )

    def resolve(self, office="mp", year=2025, translation="esv", abbreviated=False):
        return alternate_first_lesson(self.day, office, self.settings, year, translation, abbreviated)

    def module(self, year=2025, rank=5):
        office = SimpleNamespace(
            office_readings=self.day,
            readings=self.day.readings,
            settings=self.settings,
            date=SimpleNamespace(
                date=datetime.date(year, 2, 23), primary=SimpleNamespace(rank=SimpleNamespace(precedence_rank=rank))
            ),
        )
        return ReadingModule(office)

    def test_default_and_unknown_values_do_not_substitute(self):
        for value in ("appointed", "invalid", None):
            self.settings["apocrypha_readings"] = value
            self.assertIsNone(self.resolve())
        del self.settings["apocrypha_readings"]
        self.assertIsNone(self.resolve())

    def test_both_offices_are_complementary(self):
        self.assertEqual(self.resolve("mp").passage, self.morning.passage)
        self.assertEqual(self.resolve("ep").passage, self.evening.passage)
        self.assertEqual(self.resolve("ep").testament, "OT")
        self.day.refresh_from_db()
        self.assertEqual(self.day.ep_reading_1, "Baruch 4")
        self.assertEqual((self.day.mp_psalms, self.day.ep_psalms), ("1", "2"))

    def test_dc_and_ap_are_equivalent(self):
        for tag in ("DC", "AP"):
            self.day.ep_reading_1_testament = tag
            self.assertIsNotNone(self.resolve())

    def test_reversed_donor_direction(self):
        self.day.mp_reading_1, self.day.ep_reading_1 = self.day.ep_reading_1, self.day.mp_reading_1
        self.day.mp_reading_1_testament, self.day.ep_reading_1_testament = "DC", "OT"
        self.mapping.donor_office = "ep"
        self.mapping.save()
        self.assertEqual(self.resolve("mp").passage, self.morning.passage)
        self.assertEqual(self.resolve("ep").passage, self.evening.passage)

    def test_two_year_odd_canonical_unchanged_even_ap_replaced_whole(self):
        self.settings["reading_cycle"] = "2"
        for office in ("mp", "ep"):
            self.assertIsNone(self.resolve(office, 2025))
            self.assertEqual(self.resolve(office, 2026).passage, self.whole.passage)

    def test_two_year_odd_ap_replaced_for_reversed_donor(self):
        self.settings["reading_cycle"] = "2"
        self.day.mp_reading_1, self.day.ep_reading_1 = "Baruch 4", "Exodus 3"
        self.day.mp_reading_1_testament, self.day.ep_reading_1_testament = "AP", "OT"
        self.mapping.donor_office = "ep"
        self.mapping.save()
        for office in ("mp", "ep"):
            self.assertEqual(self.resolve(office, 2025).passage, self.whole.passage)
            self.assertIsNone(self.resolve(office, 2026))

    def test_abbreviated_without_short_donor_uses_full_splits(self):
        self.assertEqual(self.resolve(abbreviated=True).passage, self.morning.passage)

    def test_abbreviated_splits_and_two_year_whole(self):
        short_whole = Scripture.objects.create(passage="Exodus 3:7-22", esv="<p>short whole</p>")
        mp = Scripture.objects.create(passage="Exodus 3:7-12", esv="<p>short morning</p>")
        ep = Scripture.objects.create(passage="Exodus 3:13-22 short", esv="<p>short evening</p>")
        self.mapping.short_whole, self.mapping.short_morning, self.mapping.short_evening = short_whole, mp, ep
        self.mapping.save()
        self.day.mp_reading_1_abbreviated = short_whole.passage
        self.assertEqual(self.resolve(abbreviated=True).scripture, mp)
        self.assertEqual(self.resolve("ep", abbreviated=True).scripture, ep)
        self.settings["reading_cycle"] = "2"
        self.assertEqual(self.resolve(year=2026, abbreviated=True).scripture, short_whole)

    def test_missing_mapping_and_ordinary_day_fall_back(self):
        self.mapping.delete()
        self.assertIsNone(self.resolve())
        self.day.ep_reading_1_testament = "OT"
        self.assertIsNone(self.resolve())

    def test_missing_one_portion_text_falls_back_for_both(self):
        self.evening.esv = None
        self.evening.nrsvce = "-"
        self.evening.save()
        self.assertIsNone(self.resolve("mp"))
        self.assertIsNone(self.resolve("ep"))

    def test_empty_markup_does_not_count_as_replacement_text(self):
        self.evening.esv = "<p></p>"
        self.evening.nrsvce = "<h3>Heading only</h3><p> </p>"
        self.evening.save()
        self.assertIsNone(self.resolve("mp"))
        self.assertIsNone(self.resolve("ep"))

    def test_stale_mapping_falls_back(self):
        self.day.mp_reading_1 = "Exodus 4"
        self.assertIsNone(self.resolve())

    def test_translations_and_fallback(self):
        self.morning.kjv = "<p>KJV portion</p>"
        self.morning.save()
        self.assertEqual(self.resolve(translation="kjv").text, "<p>KJV portion</p>")
        self.assertIn("Fallback", self.resolve(translation="cuvs").text)
        self.assertEqual(self.resolve(translation="cuvs").translation, "nrsvce")

    @patch.object(GenericDailyOfficeSerializer, "reading_voice", return_value=None)
    @patch.object(GenericDailyOfficeSerializer, "handle_html", side_effect=lambda text, **kwargs: text)
    def test_citation_text_and_iframe_audio_use_selected_passage(self, *mocks):
        lines = self.module().get_lines_for_reading("ep", 1)
        contents = [line["content"] for line in lines]
        self.assertIn("Exodus 3:13-22", contents)
        self.assertTrue(any("Exodus%203%3A13-22" in str(c) for c in contents))
        self.assertFalse(any("Baruch" in str(c) for c in contents))
        self.assertTrue(any("English verse 13." in str(c) for c in contents))
        self.assertFalse(any("English verse 12." in str(c) for c in contents))
        self.settings["bible_translation"] = "kjv"
        contents = [line["content"] for line in self.module().get_lines_for_reading("ep", 1)]
        self.assertFalse(any("<iframe" in str(c) for c in contents))

    @patch.object(GenericDailyOfficeSerializer, "reading_voice", return_value=None)
    @patch.object(GenericDailyOfficeSerializer, "handle_html", side_effect=lambda text, **kwargs: text)
    def test_second_lesson_remains_year_selected(self, *mocks):
        self.settings["reading_cycle"] = "2"
        for year, text in [(2025, "Morning second"), (2026, "Evening second")]:
            for office in ("mp", "ep"):
                lines = self.module(year).get_lines_for_reading(office, 2)
                self.assertTrue(any(text in str(line["content"]) for line in lines))

    def test_mass_precedence_runs_before_alternate_resolution(self):
        self.settings["lectionary"] = "mass-readings"
        for rank in (1, 4):
            module = self.module(rank=rank)
            with (
                patch.object(module, "get_mass_reading", return_value=["mass"]) as mass,
                patch("office.api.views.index.alternate_first_lesson") as alternate,
            ):
                self.assertEqual(module.get_lines_for_reading("mp", 1), ["mass"])
                mass.assert_called_once_with(1)
                alternate.assert_not_called()
            self.settings["reading_length"] = "abbreviated"
            with patch.object(module, "abbreviated_mass_reading", return_value=["short mass"]):
                self.assertEqual(module.get_lines_for_reading("ep", 1), ["short mass"])
            self.settings["reading_length"] = "full"

    @patch.object(GenericDailyOfficeSerializer, "reading_voice", return_value=None)
    @patch.object(GenericDailyOfficeSerializer, "get_or_create_clip", return_value=(None, None))
    def test_speech_cache_receives_replacement_text_with_no_synthesis(self, clip, voice):
        self.module().get_lines_for_reading("ep", 1)
        self.assertTrue(clip.called)
        inputs = " ".join(call.args[0] for call in clip.call_args_list)
        self.assertIn("English verse 13.", inputs)
        self.assertNotIn("Appointed Apocrypha", inputs)
        self.assertTrue(all(call.kwargs["no_generate"] for call in clip.call_args_list))

    @patch.object(GenericDailyOfficeSerializer, "reading_voice", return_value=None)
    @patch.object(GenericDailyOfficeSerializer, "handle_html", side_effect=lambda text, **kwargs: text)
    def test_appointed_mode_preserves_both_offices(self, *mocks):
        self.settings["apocrypha_readings"] = "appointed"
        for office, citation in [("mp", "Exodus 3"), ("ep", "Baruch 4")]:
            self.assertEqual(self.module().get_lines_for_reading(office, 1)[0]["content"], citation)

    def test_readings_overview_shares_resolver(self):
        obj = SimpleNamespace(
            settings=self.settings, date=SimpleNamespace(date=datetime.date(2026, 2, 23)), translation="esv"
        )
        self.assertEqual(office_lesson_formats(obj, self.day, "mp", 1)["full"]["citation"], self.morning.passage)
        self.settings["reading_cycle"] = "2"
        self.assertEqual(office_lesson_formats(obj, self.day, "ep", 1)["full"]["citation"], self.whole.passage)
        self.assertEqual(office_lesson_formats(obj, self.day, "mp", 2)["full"]["citation"], "Romans 1")

    def test_setting_defaults_query_override_and_readings_category(self):
        request = SimpleNamespace(query_params={})
        self.assertEqual(Settings(request)["apocrypha_readings"], "appointed")
        request.query_params = {"apocrypha_readings": "alternate"}
        self.assertEqual(Settings(request)["apocrypha_readings"], "alternate")
        self.assertEqual(SETTING_UI_METADATA["apocrypha_readings"]["ui_category"], "Readings")


class ExtractionTests(TestCase):
    def test_all_reviewed_citations_cover_without_gaps_or_overlap(self):
        rows = plan()
        self.assertEqual(len(rows), 57)
        self.assertEqual(len({r["label"] for r in rows}), 57)
        for row in rows:
            for short in (False, True) if "short_verses" in row else (False,):
                verses = row["short_verses"] if short else row["verses"]
                cut = row["short_cut"] if short else row["cut"]
                parts = [{v for v in verses if v <= cut}, {v for v in verses if v > cut}]
                self.assertTrue(all(parts))
                self.assertFalse(parts[0] & parts[1])
                self.assertEqual(set(verses), parts[0] | parts[1])
                for selected in parts:
                    text = extract(marked(verses, row["chapter"]), row["chapter"], verses, selected)
                    self.assertEqual(
                        {
                            int(t["class"][1].split("-")[-1])
                            for t in BeautifulSoup(text, "html.parser").select("span.text")
                        },
                        selected,
                    )
        self.assertIn("7/4", {r["label"] for r in rows})
        self.assertEqual({r["donor"] for r in rows if r["testament"] == "NT"}, {"Acts 1:15-26", "II John 1-13"})

    def test_reviewed_nabre_versification_uses_explicit_fallback(self):
        row = next(r for r in plan() if r["donor"] == "Song of Songs 6")
        source = Scripture(
            passage=row["donor"],
            esv=marked(row["verses"], 6, book="Song"),
            nrsvce=marked(row["verses"], 6, book="Song"),
            nabre=marked(list(range(1, 13)), 6, book="Song"),
        )
        portions = scripture_texts(source, row)
        for fields in portions:
            self.assertIsNone(fields["nabre"])
            self.assertTrue(fields["nrsvce"])

    def test_partial_or_unmarked_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            extract(marked([1, 3]), 3, [1, 2, 3], [1])
        with self.assertRaisesRegex(ValueError, "Unmarked"):
            extract(marked([1, 2]) + "<p>unmarked words</p>", 3, [1, 2], [1])

    def test_multi_chunk_verse_and_poetry_retained(self):
        text = '<div class="poetry"><p><span class="text Isa-53-1">First line</span><br><span class="text Isa-53-1">second line</span><br><span class="text Isa-53-2">other verse</span></p></div>'
        result = extract(text, 53, [1, 2], [1])
        self.assertIn("First line", result)
        self.assertIn("second line", result)
        self.assertNotIn("other verse", result)
        self.assertIn('class="poetry"', result)

    def test_explicit_number_crossing_split_rejected(self):
        text = '<p><span class="text Exod-3-1"><sup class="versenum">2</sup>words</span></p>'
        with self.assertRaisesRegex(ValueError, "cross"):
            extract(text, 3, [1, 2], [1])

    def test_unavailable_donor_not_silently_seeded(self):
        row = next(r for r in plan() if r["donor"] == "Exodus 3")
        with self.assertRaisesRegex(ValueError, "ESV and NRSVCE"):
            scripture_texts(Scripture(passage="Exodus 3", esv="-"), row)


class AlternateMigrationTests(TransactionTestCase):
    """Run actual historical migrations on a fresh test DB and seeded rows."""

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("office", "0032_alternate_reading")])
        self.historical = executor.loader.project_state([("office", "0032_alternate_reading")]).apps
        self.historical.get_model("office", "Setting").objects.filter(name="apocrypha_readings").delete()

    def tearDown(self):
        # Restore leaf migration state for other tests, even after rejection tests.
        self.historical.get_model("office", "OfficeDay").objects.all().delete()
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def migrate(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("office", "0033_seed_alternate_readings")])
        return executor.loader.project_state([("office", "0033_seed_alternate_readings")]).apps

    def seed(self, **overrides):
        day = appointed_day(self.historical.get_model("office", "StandardOfficeDay"), **overrides)
        scripture = self.historical.get_model("office", "Scripture")
        whole = scripture.objects.create(
            passage="Exodus 3", esv=marked(list(range(1, 23))), nrsvce=marked(list(range(1, 23)))
        )
        return day, whole

    def test_empty_fresh_database_migrates_and_setting_appends(self):
        Setting = self.historical.get_model("office", "Setting")
        legacy = Setting.objects.create(
            name="legacy", title="Legacy", site=1, setting_type=1, order=4, setting_string_order=29
        )
        historical = self.migrate()
        new = historical.get_model("office", "Setting").objects.get(name="apocrypha_readings")
        self.assertEqual(new.setting_string_order, 30)
        legacy.refresh_from_db()
        self.assertEqual(legacy.setting_string_order, 29)
        self.assertEqual(historical.get_model("office", "AlternateReading").objects.count(), 0)

    def test_seed_existing_portion_reused_and_reverse_retains_text(self):
        day, whole = self.seed()
        row = next(r for r in plan() if r["donor"] == "Exodus 3")
        texts = scripture_texts(whole, row)
        Scripture = self.historical.get_model("office", "Scripture")
        existing = Scripture.objects.create(passage=row["mp"], **texts[0])
        original = existing.esv
        historical = self.migrate()
        Alternate = historical.get_model("office", "AlternateReading")
        mapping = Alternate.objects.get(office_day_id=day.pk)
        self.assertEqual(mapping.morning_id, existing.pk)
        with connection.schema_editor() as editor:
            forward(historical, editor)
        self.assertEqual(Alternate.objects.count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.esv, original)
        day.refresh_from_db()
        self.assertEqual(day.ep_reading_1, "Baruch 4")
        with connection.schema_editor() as editor:
            backward(historical, editor)
        self.assertTrue(Scripture.objects.filter(pk=existing.pk).exists())
        self.assertTrue(Scripture.objects.filter(passage=row["ep"]).exists())

    def test_preexisting_mapping_and_edited_retained_scripture_survive_reverse(self):
        day, whole = self.seed()
        row = next(r for r in plan() if r["donor"] == "Exodus 3")
        texts = scripture_texts(whole, row)
        Scripture = self.historical.get_model("office", "Scripture")
        Alternate = self.historical.get_model("office", "AlternateReading")
        morning = Scripture.objects.create(passage=row["mp"], **texts[0])
        evening = Scripture.objects.create(passage=row["ep"], **texts[1])
        existing = Alternate.objects.create(
            office_day_id=day.pk, donor_office="mp", whole=whole, morning=morning, evening=evening
        )
        historical = self.migrate()
        morning.esv = "<p>Administrator edit after deployment</p>"
        morning.save()
        with connection.schema_editor() as editor:
            backward(historical, editor)
        self.assertTrue(Alternate.objects.filter(pk=existing.pk).exists())
        morning.refresh_from_db()
        self.assertEqual(morning.esv, "<p>Administrator edit after deployment</p>")

    def test_conflicting_preexisting_scripture_is_not_overwritten(self):
        self.seed()
        Scripture = self.historical.get_model("office", "Scripture")
        existing = Scripture.objects.create(passage="Exodus 3:1-12", esv="<p>User text</p>")
        with self.assertRaisesRegex(ValueError, "no user text overwritten"):
            self.migrate()
        existing.refresh_from_db()
        self.assertEqual(existing.esv, "<p>User text</p>")
        self.assertFalse(Scripture.objects.filter(passage="Exodus 3:13-22").exists())

    def test_missing_whole_passage_rolls_back(self):
        appointed_day(self.historical.get_model("office", "StandardOfficeDay"))
        with self.assertRaisesRegex(ValueError, "exactly one existing"):
            self.migrate()
        self.assertEqual(self.historical.get_model("office", "AlternateReading").objects.count(), 0)

    def test_dc_and_holy_day_base_rows_are_seeded(self):
        day, whole = self.seed(ep_reading_1_testament="DC")
        # OfficeDay is the concrete parent shared by annual and holy-day records.
        base = self.historical.get_model("office", "OfficeDay")
        holy = appointed_day(base, ep_reading_1_testament="DC")
        historical = self.migrate()
        self.assertEqual(historical.get_model("office", "AlternateReading").objects.count(), 2)
