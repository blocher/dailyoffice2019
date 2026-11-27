import json
from io import StringIO
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from psalter.chant import dictionary
from psalter.chant.notation import NotationError, parse, tail_signature, validate
from psalter.chant.pointing import (
    ACCENT,
    FINAL,
    INTONATION,
    PREPARATORY,
    RECITE,
    RETURN,
    describe,
    point,
    point_verse,
    rhythm,
    segments,
)
from psalter.chant.service import assess, chant_for_verse, point_psalm
from psalter.chant.tones import DEFAULT_TONE, TONES, get_tone
from psalter.management.commands.point_psalms import parse_selection
from psalter.models import Psalm, PsalmVerse, PsalmVersePointing
from psalter.utils import psalm_api_lines


def roles(notation, tone_code, mediation, first_verse=False):
    tone = TONES[tone_code]
    part = tone.mediation if mediation else tone.ending
    pointed = point(notation, part, mediation=mediation, first_verse=first_verse)
    return [(s.text.strip(".,;:"), s.role) for s in pointed.syllables], pointed


class NotationTests(SimpleTestCase):
    def test_parse_marks_syllables_and_accents(self):
        syllables = parse("The +Lord is my +shep/herd;")
        self.assertEqual([s.text for s in syllables], ["The", "Lord", "is", "my", "shep", "herd;"])
        self.assertEqual([s.accent for s in syllables], [False, True, False, False, True, False])
        self.assertTrue(syllables[4].word_start)
        self.assertFalse(syllables[5].word_start)

    def test_validate_requires_the_same_text(self):
        validate("The +Lord is my +shep/herd;", "The Lord is my shepherd;")
        with self.assertRaises(NotationError):
            validate("The +Lord is our +shep/herd;", "The Lord is my shepherd;")
        with self.assertRaises(NotationError):
            validate("The +Lord is my +shep//herd;", "The Lord is my shepherd;")

    def test_tail_signature(self):
        self.assertEqual(tail_signature("and +bring me +forth in the +paths of +right/eous/ness"), ".x.x..")


class PointingTests(SimpleTestCase):
    """Examples from Briggs & Frere, A Manual of Plainsong, Introduction II."""

    def test_trochaic_ending(self):
        result, pointed = roles("the +Lord with +ho/ly +wor/ship.", "8.G", mediation=False)
        self.assertEqual(
            result[-4:],
            [("ho", PREPARATORY), ("ly", PREPARATORY), ("wor", ACCENT), ("ship", FINAL)],
        )
        self.assertEqual(pointed.inflection_start, 3)

    def test_dactylic_ending_fills_the_redundant_syllable(self):
        result, _ = roles("dwell to/+geth/er in +u/ni/ty.", "8.G", mediation=False)
        self.assertEqual(
            result[-5:],
            [("er", PREPARATORY), ("in", PREPARATORY), ("u", ACCENT), ("ni", RETURN), ("ty", FINAL)],
        )

    def test_accent_four_from_the_end_falls_back_to_the_penultimate(self):
        result, pointed = roles("un/to thy +tes/ti/mo/nies.", "8.G", mediation=False)
        self.assertEqual(result[-3:], [("ti", PREPARATORY), ("mo", ACCENT), ("nies", FINAL)])
        self.assertEqual(pointed.warnings, [])

    def test_stressed_final_syllable_of_an_ending_takes_the_final_note(self):
        result, _ = roles("in the +Name of the +Lord.", "8.G", mediation=False)
        self.assertEqual(result[-3:], [("of", PREPARATORY), ("the", ACCENT), ("Lord", FINAL)])

    def test_fifth_tone_has_two_accents_in_the_ending(self):
        result, _ = roles("the +Lord with +ho/ly +wor/ship.", "5.a", mediation=False)
        self.assertEqual(result[-4:], [("ho", ACCENT), ("ly", RETURN), ("wor", ACCENT), ("ship", FINAL)])
        result, _ = roles("dwell to/+geth/er in +u/ni/ty.", "5.a", mediation=False)
        self.assertEqual(
            result[-6:],
            [("geth", ACCENT), ("er", RETURN), ("in", RETURN), ("u", ACCENT), ("ni", RETURN), ("ty", FINAL)],
        )

    def test_rising_mediation_returns_to_the_reciting_note(self):
        result, _ = roles("no +plea/sure in +wick/ed/ness", "8.G", mediation=True)
        self.assertEqual(result[-3:], [("wick", ACCENT), ("ed", RETURN), ("ness", FINAL)])

    def test_abrupt_mediation_on_a_stressed_monosyllable(self):
        result, pointed = roles("mine +eyes have +seen", "8.G", mediation=True)
        self.assertEqual(result[-1], ("seen", ACCENT))
        self.assertEqual(pointed.syllables[-1].notes, "kj.")
        self.assertEqual(result[-2], ("have", RECITE))

    def test_intonation_on_the_first_verse_only(self):
        result, _ = roles("The +Lord is my +shep/herd;", "8.G", mediation=True, first_verse=True)
        self.assertEqual(result[:2], [("The", INTONATION), ("Lord", INTONATION)])
        result, _ = roles("The +Lord is my +shep/herd;", "8.G", mediation=True)
        self.assertEqual(result[0], ("The", RECITE))

    def test_short_half_verse_drops_the_first_notes(self):
        result, pointed = roles("+Praise the +Lord.", "8.G", mediation=False)
        self.assertEqual(result, [("Praise", ACCENT), ("the", RETURN), ("Lord", FINAL)])
        self.assertTrue(pointed.warnings)

    def test_every_tone_points_a_verse(self):
        for code, tone in TONES.items():
            if tone.book:
                continue  # pointed from the book's marks; see BookPointingTests
            with self.subTest(tone=code):
                first = point("and +bring me +forth in the +paths of +right/eous/ness", tone.mediation, mediation=True)
                second = point("for his +Name's +sake.", tone.ending, mediation=False)
                self.assertIn(ACCENT, first.roles())
                self.assertEqual(second.syllables[-1].role, FINAL)

    def test_segments_mark_only_letters(self):
        pointed = point("The +Lord is my +shep/herd;", TONES["8.G"].mediation, mediation=True)
        items = segments(pointed)
        self.assertIn({"t": "", "r": "bar"}, items)
        self.assertIn({"t": "shep", "r": "accent"}, items)
        self.assertEqual(items[-1], {"t": ";", "r": ""})
        self.assertEqual("".join(i["t"] for i in items), "The Lord is my shepherd;")

    def test_segments_carry_pitches_for_playback(self):
        tone = TONES["8.G"]
        pointed = point("The +Lord is my +shep/herd;", tone.mediation, mediation=True, first_verse=True)
        sung = [s for s in segments(pointed, tone.clef) if "p" in s]
        self.assertEqual([s["t"] for s in sung], ["The", "Lord", "is", "my", "shep", "herd"])
        # Intonation G A, reciting C, the rise to D on the accent, and a long C.
        self.assertEqual([s["p"] for s in sung], [[55], [57], [60], [60], [62], [60]])
        # The cadence broadens to the last syllable; the long final note
        # before the asterisk a little less.
        self.assertEqual(sung[-1]["d"], [2.25])
        self.assertEqual(sung[-2]["d"], [1.25])
        self.assertEqual(sung[2]["d"], [0.625])  # quicker on the reciting note

    def test_rhythm_breathes_at_commas_but_not_at_the_end(self):
        tone = TONES["8.G"]
        pointed = point("Yea, though I +walk through the +val/ley,", tone.mediation, mediation=True)
        timing = rhythm(pointed)
        self.assertEqual(timing[0], (1, 0.75))  # "Yea," held before the breath, not clipped
        self.assertEqual(timing[1], (0.625, 0))
        self.assertEqual(timing[3], (0.875, 0))  # "+walk": stressed, so a little longer
        self.assertEqual(timing[-1][1], 0)  # the asterisk already rests
        sung = [s for s in segments(pointed, tone.clef) if "p" in s]
        self.assertEqual(sung[0]["w"], 0.75)
        self.assertNotIn("w", sung[1])

    def test_a_short_mediation_still_holds_its_last_syllable(self):
        from psalter.chant.tones import gabc_pitches

        tone = get_tone("B4.4")
        final = sum(p for _, p in gabc_pitches(tone.mediation.cadence[-1].notes, tone.clef))
        # Too short for the whole mediation: the book leaves the last note out.
        short, _ = point_verse("He shall re/^fresh my ^soul", "and ^so ^on.", tone)
        self.assertEqual(sum(p for _, p in gabc_pitches(short.syllables[-1].notes, tone.clef)), final)
        self.assertEqual(
            rhythm(short)[-1], rhythm(point_verse("in your ^ho/ly ^pla/ces;", "and ^so ^on.", tone)[0])[-1]
        )

    def test_book_pointing_recites_with_the_dictionary_stress(self):
        from psalter.chant.pointing import spoken_stress

        tone = get_tone("B4.4")
        first, _ = point_verse("the val/ley of the shad/ow of ^death, I ^will,", "and ^so ^on.", tone)
        stress = dict(zip([s.text for s in first.syllables], spoken_stress(first)))
        self.assertTrue(stress["val"])
        self.assertFalse(stress["ley"])
        self.assertFalse(stress["of"])
        self.assertTrue(stress["shad"])

    def test_cadence_broadens_gradually_and_more_at_the_end(self):
        from psalter.chant.pointing import ENDING_BROADENING, MEDIATION_BROADENING

        tone = TONES["8.G"]
        first, second = point_verse("He shall +feed me in +green +pas/tures", GOOD[2][1], tone)
        for half, (start, end) in ((first, MEDIATION_BROADENING), (second, ENDING_BROADENING)):
            scales = [
                scale for s, (scale, _) in zip(half.syllables, rhythm(half)) if s.role not in ("recite", "final")
            ]
            self.assertEqual(scales[-1], end)
            if len(scales) > 1:
                self.assertEqual(scales[0], start)
            self.assertEqual(scales, sorted(scales))
        self.assertLess(MEDIATION_BROADENING[1], ENDING_BROADENING[1])

    def test_describe(self):
        pointed = point("the +Lord with +ho/ly +wor/ship.", TONES["8.G"].ending, mediation=False)
        self.assertEqual(describe(pointed), "the Lord with | [ho]-[ly] WOR-ship.")

    def test_unknown_tone_uses_the_default(self):
        self.assertEqual(get_tone("").code, DEFAULT_TONE)
        self.assertEqual(get_tone("nonsense").code, DEFAULT_TONE)


class PitchTests(SimpleTestCase):
    def test_gabc_pitches(self):
        from psalter.chant.tones import gabc_pitches

        self.assertEqual(gabc_pitches("j.", "c4"), [(60, 2)])
        self.assertEqual(gabc_pitches("ixi", "c4"), [(58, 1)])  # B flat
        self.assertEqual(gabc_pitches("gvFED.", "c4"), [(55, 1), (53, 1), (52, 1), (50, 2)])
        self.assertEqual(gabc_pitches("h", "c3"), [(60, 1)])
        self.assertEqual(gabc_pitches("gf..", "c4"), [(55, 2), (53, 2)])
        self.assertEqual(gabc_pitches("h", "f3"), [(65, 1)])

    def test_score_lines_up_with_the_demo(self):
        tone = TONES["8.G"].as_dict()
        score = tone["score"]
        self.assertEqual(score["clef"], "c4")
        self.assertEqual(
            [g["role"] for g in score["first_half"]],
            ["intonation", "intonation", "tenor", "accent", "return", "note"],
        )
        self.assertEqual([g["n"] for g in score["second_half"]], ["j", "i", "j", "h", "g", "g."])
        # The demo repeats the tenor three times; otherwise the same groups.
        self.assertEqual(len(tone["demo"]["first_half"]), len(score["first_half"]) + 2)

    def test_every_tone_has_a_demo(self):
        for code, tone in TONES.items():
            with self.subTest(tone=code):
                demo = tone.as_dict()["demo"]
                self.assertTrue(demo["first_half"] and demo["second_half"])


class DictionaryTests(SimpleTestCase):
    def test_notation_keeps_the_text(self):
        for text in [
            "and bring me forth in the paths of righteousness for his Name's sake.",
            "Even though I walk through the valley of the shadow of death, I will fear no evil,",
            "He shall refresh my soul — and well-being",
        ]:
            with self.subTest(text=text):
                validate(dictionary.notate(text), text)

    def test_stress_and_syllables(self):
        self.assertEqual(dictionary.notate("the valley of comfort"), "the +val/ley of +com/fort")
        self.assertEqual(dictionary.syllabify("refresh", 2), ["re", "fresh"])
        self.assertEqual(dictionary.syllabify("righteous", 2), ["right", "eous"])
        self.assertEqual(dictionary.word_check("testimonies"), (4, 0))
        self.assertIsNone(dictionary.word_check("Lord"))


def make_psalm(number=23, verses=None):
    psalm = Psalm.objects.create(number=number, latin_title="Dominus regit me")
    verses = verses or [
        (1, "The Lord is my shepherd;", "therefore I can lack nothing."),
        (2, "He shall feed me in green pastures", "and lead me forth beside the waters of comfort."),
    ]
    for verse_number, first, second in verses:
        PsalmVerse.objects.create(psalm=psalm, number=verse_number, first_half=first, second_half=second)
    return psalm


GOOD = {
    1: ("The +Lord is my +shep/herd;", "+there/fore I can +lack +noth/ing."),
    2: ("He shall +feed me in +green +pas/tures", "and +lead me +forth be/+side the +wa/ters of +com/fort."),
}


class FakeClient:
    """Stands in for the OpenAI client, returning set answers in turn."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        verses = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        payload = {
            "verses": [
                {"number": n, "first_half": a, "second_half": b, "confidence": 0.9, "note": ""}
                for n, (a, b) in verses.items()
            ]
        }
        message = SimpleNamespace(content=json.dumps(payload))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class ServiceTests(TestCase):
    def setUp(self):
        self.psalm = make_psalm()
        self.verse = PsalmVerse.objects.get(psalm=self.psalm, number=2)

    def run_(self, first, second, confidence=0.9):
        return {"first_half": first, "second_half": second, "confidence": confidence, "note": ""}

    def test_agreeing_runs_are_trusted(self):
        result = assess(self.verse, [self.run_(*GOOD[2]), self.run_(*GOOD[2])])
        self.assertEqual(result.status, PsalmVersePointing.AGREED, result.notes)

    def test_disagreeing_runs_need_review(self):
        other = (GOOD[2][0], "and +lead me +forth be/+side the +wa/ters of com/+fort.")
        result = assess(self.verse, [self.run_(*GOOD[2]), self.run_(*other)])
        self.assertEqual(result.status, PsalmVersePointing.NEEDS_REVIEW)
        self.assertTrue(any("disagree" in n for n in result.notes))

    def test_dictionary_disagreement_asks_for_a_check(self):
        odd = (GOOD[2][0], "and +lead me +forth be/+side the +wa/ters of com/+fort.")
        result = assess(self.verse, [self.run_(*odd)])
        self.assertEqual(result.status, PsalmVersePointing.CHECK)
        self.assertTrue(any("comfort" in n for n in result.notes))

    def test_answers_that_change_the_text_are_ignored(self):
        changed = (GOOD[2][0], "and +lead us +forth be/+side the +wa/ters of +com/fort.")
        result = assess(self.verse, [self.run_(*changed)])
        self.assertEqual(result.status, PsalmVersePointing.NEEDS_REVIEW)
        self.assertEqual(result.second_half, dictionary.notate(self.verse.second_half))

    def test_no_ai_uses_the_dictionary(self):
        result = assess(self.verse, [])
        self.assertEqual(result.status, PsalmVersePointing.DICTIONARY)

    def test_point_psalm_saves_and_keeps_approved_verses(self):
        client = FakeClient(GOOD)
        results = point_psalm(self.psalm, runs=2, client=client, model="test-model")
        self.assertEqual(len(results), 2)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(client.calls[0]["model"], "test-model")
        pointing = PsalmVersePointing.objects.get(verse=self.verse)
        self.assertEqual(pointing.second_half_stress, GOOD[2][1])
        self.assertEqual(pointing.ai_model, "test-model")
        self.assertEqual(len(pointing.ai_runs), 2)

        pointing.status = PsalmVersePointing.APPROVED
        pointing.save()
        results = point_psalm(self.psalm, use_ai=False)
        self.assertEqual([r.verse.number for r in results], [1])
        pointing.refresh_from_db()
        self.assertEqual(pointing.status, PsalmVersePointing.APPROVED)

    def test_pointing_clears_caches_and_tells_devices(self):
        from office.models import ContentChange

        with self.captureOnCommitCallbacks(execute=True):
            point_psalm(self.psalm, use_ai=False)
        change = ContentChange.objects.latest("created")
        self.assertIn("Psalm 23", change.note)
        self.assertIsNone(change.start_date)

    def test_chant_for_verse(self):
        self.assertIsNone(chant_for_verse(self.verse))
        point_psalm(self.psalm, client=FakeClient(GOOD), runs=1)
        verse = PsalmVerse.objects.select_related("psalm", "pointing").get(pk=self.verse.pk)
        chant = chant_for_verse(verse)
        self.assertEqual(chant["tone"], DEFAULT_TONE)
        self.assertEqual("".join(s["t"] for s in chant["second_half"]), verse.second_half)
        # Marks go stale if the verse text is edited afterwards.
        verse.second_half = "and lead me forth beside still waters."
        self.assertIsNone(chant_for_verse(verse))


class CommandTests(TestCase):
    def setUp(self):
        self.psalm = make_psalm()

    def test_selection(self):
        self.assertEqual(parse_selection(["23", "95,100-102"]), [23, 95, 100, 101, 102])
        with self.assertRaises(CommandError):
            parse_selection(["151"])
        with self.assertRaises(CommandError):
            parse_selection(["10-2"])

    def test_requires_a_choice_of_psalms(self):
        with self.assertRaises(CommandError):
            call_command("point_psalms", stdout=StringIO())

    def test_dictionary_run_saves_and_sets_the_tone(self):
        out = StringIO()
        call_command("point_psalms", "23", "--no-ai", "--tone", "5.a", stdout=out)
        self.assertIn("Saved: 2 dictionary.", out.getvalue())
        self.psalm.refresh_from_db()
        self.assertEqual(self.psalm.chant_tone, "5.a")
        self.assertEqual(PsalmVersePointing.objects.count(), 2)

    def test_dry_run_saves_nothing(self):
        out = StringIO()
        call_command("point_psalms", "23", "--no-ai", "--dry-run", stdout=out)
        self.assertIn("Would save", out.getvalue())
        self.assertEqual(PsalmVersePointing.objects.count(), 0)

    def test_missing_psalm(self):
        with self.assertRaises(CommandError):
            call_command("point_psalms", "24", "--no-ai", stdout=StringIO())


class DisplayTests(TestCase):
    def setUp(self):
        self.psalm = make_psalm()
        point_psalm(self.psalm, client=FakeClient(GOOD), runs=1)

    def test_psalm_api_includes_chant(self):
        response = self.client.get("/api/v1/psalms/23/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["chant_tone"]["code"], DEFAULT_TONE)
        first = data["verses"][0]["chant"]["first_half"][0]
        self.assertEqual((first["t"], first["r"], first["p"]), ("The", "intonation", [55]))
        self.assertEqual(data["chant_tone"]["tenor"], 60)
        self.assertTrue(data["chant_tone"]["demo"]["second_half"])

    def test_psalm_list_leaves_out_the_chant(self):
        response = self.client.get("/api/v1/psalms")
        self.assertEqual(response.status_code, 200)
        psalm = response.json()[0]
        self.assertEqual(psalm["number"], 23)
        self.assertNotIn("chant_recording", psalm)
        self.assertNotIn("chant", psalm["verses"][0])
        self.assertTrue(psalm["verses"][0]["first_half"])

    def test_office_lines_carry_chant_for_contemporary_text_only(self):
        verses = PsalmVerse.objects.filter(psalm=self.psalm).select_related("psalm", "pointing").order_by("number")
        lines = psalm_api_lines("23", verses)
        psalm_lines = [line for line in lines if line.get("preface") or line.get("indented") == "indent"]
        self.assertTrue(all("chant" in line for line in psalm_lines))
        # The office's first verse gets the intonation even mid-psalm.
        later = psalm_api_lines("23:2", verses.filter(number=2))
        first_line = next(line for line in later if line.get("preface"))
        self.assertEqual(first_line["chant"][0]["r"], "intonation")
        traditional = psalm_api_lines("23", verses, language_style="traditional")
        self.assertFalse(any("chant" in line for line in traditional))


class AdminTests(TestCase):
    def setUp(self):
        self.psalm = make_psalm()
        point_psalm(self.psalm, use_ai=False)
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(user)
        self.pointing = PsalmVersePointing.objects.get(verse__number=2)

    def test_pages_render(self):
        self.assertEqual(self.client.get(reverse("admin:psalter_psalm_changelist")).status_code, 200)
        response = self.client.get(reverse("admin:psalter_psalm_change", args=[self.psalm.pk]))
        self.assertContains(response, "chant-preview")
        self.assertContains(response, "class='accent'")
        self.assertEqual(self.client.get(reverse("admin:psalter_psalmversepointing_changelist")).status_code, 200)
        url = reverse("admin:psalter_psalmversepointing_change", args=[self.pointing.pk])
        self.assertContains(self.client.get(url), "Syllables and marks")

    def test_editing_validates_and_approves(self):
        url = reverse("admin:psalter_psalmversepointing_change", args=[self.pointing.pk])
        data = {
            "first_half_stress": GOOD[2][0],
            "second_half_stress": "and +lead us +forth",
            "status": self.pointing.status,
        }
        response = self.client.post(url, data)
        self.assertContains(response, "does not match the verse text")
        edited = "and +lead me forth be/+side the +wa/ters of +com/fort."
        self.assertNotEqual(self.pointing.second_half_stress, edited)
        data["second_half_stress"] = edited
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.pointing.refresh_from_db()
        self.assertEqual(self.pointing.status, PsalmVersePointing.APPROVED)
        self.assertEqual(self.pointing.second_half_stress, edited)


class ExportTests(TestCase):
    def setUp(self):
        self.psalm = make_psalm()
        point_psalm(self.psalm, client=FakeClient(GOOD), runs=1)

    def test_notes_follow_synthesizer_v_lyric_conventions(self):
        from psalter.chant.export import psalm_notes

        notes, length = psalm_notes(self.psalm, tenor=60)
        lyrics = [n.lyric for n in notes[:7]]
        # "shep-herd" is one word over two notes; "herd" takes "+".
        self.assertEqual(lyrics[:6], ["The", "Lord", "is", "my", "shepherd", "+"])
        self.assertEqual(notes[2].pitch, 60)  # the reciting note where asked
        self.assertEqual(notes[4].pitch, 62)  # the rise on the accent
        # A rest of three pulses at the asterisk.
        first_half_end = notes[5].onset + notes[5].pulses
        self.assertEqual(notes[6].onset, first_half_end + 3)
        self.assertEqual(length, notes[-1].onset + notes[-1].pulses)

    def test_lyrics_keep_small_capitals_and_apostrophes(self):
        from psalter.chant.export import _clean

        self.assertEqual(_clean("Lᴏʀᴅ"), "Lord")
        self.assertEqual(_clean("Name’s"), "Name's")
        self.assertEqual(_clean("“comfort.”"), "comfort")

    def test_held_syllables_take_a_dash(self):
        from psalter.chant.export import psalm_notes

        notes, _ = psalm_notes(self.psalm, tone=TONES["1.D"])
        last = [n for n in notes if n.verse == 1 and n.half == 1][-4:]
        # Tone I.D ends on a group of four notes on one syllable.
        self.assertEqual([n.lyric for n in last][1:], ["-", "-", "-"])

    def test_command_writes_a_script_and_musicxml(self):
        import tempfile
        from pathlib import Path
        from xml.dom import minidom

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "psalm.js"
            call_command("export_chant", "23", "--out", str(script), stdout=StringIO())
            text = script.read_text()
            self.assertIn("function main()", text)
            self.assertIn('"shepherd"', text)
            # Notes within a phrase touch, so each syllable is not re-attacked.
            self.assertIn("Math.round(n[1] * PULSE)", text)
            xml = Path(directory) / "psalm.musicxml"
            call_command("export_chant", "23", "--format", "musicxml", "--out", str(xml), stdout=StringIO())
            document = minidom.parse(str(xml))
            lyrics = [t.firstChild.data for t in document.getElementsByTagName("text")]
            self.assertEqual(lyrics[:6], ["The", "Lord", "is", "my", "shep", "herd"])
            # An unstressed reciting syllable is five of sixteen divisions to
            # the quarter; the accent, at the end of the cadence, ten.
            # (Lengths with no single note value are tied notes; add them up.)
            durations = []
            for n in document.getElementsByTagName("note"):
                units = int(n.getElementsByTagName("duration")[0].firstChild.data)
                tied = any(tie.getAttribute("type") == "stop" for tie in n.getElementsByTagName("tie"))
                if tied:
                    durations[-1] += units
                else:
                    durations.append(units)
            self.assertEqual(durations[2], 5)
            self.assertEqual(durations[4], 10)

    def test_musicxml_respells_words_cantai_would_mispronounce(self):
        from xml.dom import minidom

        from psalter.chant.export import SungNote, to_musicxml
        from psalter.chant.tones import get_tone

        def note(onset, lyric, syllable, syllabic, verse):
            return SungNote(
                onset=onset, pulses=1, pitch=57, lyric=lyric, syllable=syllable, syllabic=syllabic, verse=verse, half=0
            )

        notes = [
            note(0, "wind", "wind", "single", 1),
            note(1, "Hasten", "Has", "begin", 1),
            note(2, "+", "ten", "end", 1),
            note(3, "-", "", "", 1),
            note(5, "bow", "bow", "single", 7),  # bow down: sung as printed
        ]
        xml = to_musicxml(self.psalm, notes, tone=get_tone("B8.1"), pulse_seconds=0.38)
        lyrics = [t.firstChild.data for t in minidom.parseString(xml).getElementsByTagName("text")]
        self.assertEqual(lyrics, ["winned", "Hay", "sen", "bow"])
        # The bow that shoots is respelled only where the verse means it.
        psalm = SimpleNamespace(number=7)
        xml = to_musicxml(psalm, [note(0, "bow", "bow", "single", 13)], tone=get_tone("B8.1"), pulse_seconds=0.38)
        self.assertIn("<text>beau</text>", xml)

    def test_recording_key_changes_only_where_words_are_respelled(self):
        from psalter.chant.export import recording_key
        from psalter.chant.pronunciation import respellings_in

        verses = list(self.psalm.psalmverse_set.select_related("pointing").order_by("number"))
        # Verse 2 says "lead me forth", which Cantai would sing as the metal.
        self.assertEqual(respellings_in(23, verses), [(2, "lead", "leed")])
        self.assertEqual(respellings_in(23, verses[:1]), [])
        self.assertNotEqual(recording_key(self.psalm, verses, 0.38), recording_key(self.psalm, verses[:1], 0.38))

    def test_musicxml_breathes_at_a_comma_inside_a_half_verse(self):
        from xml.dom import minidom

        from psalter.chant.export import SungNote, to_musicxml
        from psalter.chant.tones import get_tone

        # "death, I": half a pulse's breath after the comma, same half-verse.
        notes = [
            SungNote(
                onset=0, pulses=0.75, pitch=57, lyric="death", syllable="death", syllabic="single", verse=4, half=0
            ),
            SungNote(onset=1.25, pulses=0.75, pitch=57, lyric="I", syllable="I", syllabic="single", verse=4, half=0),
        ]
        xml = to_musicxml(self.psalm, notes, tone=get_tone("B8.1"), pulse_seconds=0.38)
        kinds = [
            "rest" if n.getElementsByTagName("rest") else "note"
            for n in minidom.parseString(xml).getElementsByTagName("note")
        ]
        self.assertEqual(kinds, ["note", "rest", "note"])

    def test_musicxml_swells_to_the_cadence_and_falls_away(self):
        import re

        from psalter.chant.export import SungNote, to_musicxml
        from psalter.chant.tones import get_tone

        def sung(onset, cadence, half=0):
            return SungNote(
                onset=onset,
                pulses=1,
                pitch=57,
                lyric="la",
                syllable="la",
                syllabic="single",
                verse=1,
                half=half,
                cadence=cadence,
            )

        def shape(notes):
            xml = to_musicxml(self.psalm, notes, tone=get_tone("B8.1"), pulse_seconds=0.38)
            events = re.findall(r'<wedge type="(\w+)"/>|<(note)>|<dynamics><(\w+)/>', xml)
            return [wedge or note or dynamic for wedge, note, dynamic in events]

        # A recitation of four pulses swells; one of two (the second half)
        # only falls away, and each half starts again from mp.
        long = [sung(onset, False) for onset in range(4)] + [sung(4, True), sung(5, True)]
        short = [sung(7, False, 1), sung(8, False, 1), sung(9, True, 1), sung(10, True, 1)]
        self.assertEqual(
            shape(long + short),
            ["mp", "crescendo"]
            + ["note"] * 4
            + ["stop", "diminuendo", "note", "note", "stop"]
            + ["note", "mp", "note", "note", "diminuendo", "note", "note", "stop"],
        )

    def test_musescore_score_gets_the_cantai_voice(self):
        import tempfile
        import zipfile
        from pathlib import Path

        from psalter.chant.export import CANTAI_MALE_CHOIR, set_musescore_sound, sound_from_score

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "psalm.mscz"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("psalm.mscx", "<museScore/>")
                archive.writestr(
                    "audiosettings.json", json.dumps({"activeSoundProfile": "MuseScore Basic", "tracks": []})
                )
            set_musescore_sound(path)
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(archive.read("psalm.mscx"), b"<museScore/>")
                settings = json.loads(archive.read("audiosettings.json"))
            self.assertEqual(settings["tracks"][0]["instrumentId"], "tenor")
            self.assertEqual(settings["tracks"][0]["out"]["auxSends"][0]["signalAmount"], 0.43)
            self.assertEqual(sound_from_score(path), CANTAI_MALE_CHOIR)

    def test_lengths_without_a_note_value_are_tied(self):
        from psalter.chant.export import _split

        self.assertEqual(_split(0.75), [6])
        self.assertEqual(_split(0.625), [4, 1])
        self.assertEqual(_split(1.25), [8, 2])
        self.assertEqual(_split(3), [24])

    def test_command_needs_a_pointed_psalm(self):
        Psalm.objects.create(number=24)
        with self.assertRaises(CommandError):
            call_command("export_chant", "24", stdout=StringIO())


class RecordingTests(TestCase):
    def setUp(self):
        self.psalm = make_psalm()
        point_psalm(self.psalm, client=FakeClient(GOOD), runs=1)

    def recording(self):
        from office.api.serializers import PsalmSerializer
        from office.api.views.resources import PsalmsViewSet

        psalm = PsalmsViewSet.queryset.get(pk=self.psalm.pk)
        return PsalmSerializer(psalm).data["chant_recording"]

    def record(self):
        from psalter.chant.export import recording_key

        verses = list(self.psalm.psalmverse_set.select_related("pointing").order_by("number"))
        self.psalm.chant_recording.name = "chant/psalm-23.mp3"
        self.psalm.chant_recording_pulse = 0.38
        self.psalm.chant_recording_key = recording_key(self.psalm, verses, 0.38)
        self.psalm.chant_recording_voice = "Cantai men's choir"
        self.psalm.save()

    def test_no_recording(self):
        self.assertIsNone(self.recording())

    def test_recording_while_it_matches_the_pointing(self):
        self.record()
        self.assertEqual(
            self.recording(),
            {"url": "/uploads/chant/psalm-23.mp3", "pulse": 0.38, "voice": "Cantai men's choir"},
        )
        # Re-pointing a verse puts the recording out of time with the text.
        pointing = PsalmVersePointing.objects.filter(verse__psalm=self.psalm).first()
        pointing.second_half_stress = pointing.second_half_stress.replace("+lack", "lack")
        pointing.save()
        self.assertIsNone(self.recording())


# --- The St. Bernard Psalter --------------------------------------------------


def book_roles(notation, tone_code, mediation, first_verse=False):
    from psalter.chant.pointing import point_marked

    tone = TONES[tone_code]
    part = tone.mediation if mediation else tone.ending
    pointed = point_marked(notation, part, mediation=mediation, first_verse=first_verse)
    sung = [(s.text.strip(".,;:"), s.role) for s in pointed.syllables[pointed.inflection_start :]]
    return sung, pointed


class BookNotationTests(SimpleTestCase):
    def test_book_marks_parse_and_strip(self):
        syllables = parse("and ^hear ~my =prayer.")
        self.assertEqual([s.text for s in syllables], ["and", "hear", "my", "prayer."])
        self.assertEqual([(s.pointed, s.slur, s.double) for s in syllables][1:], [(1, 0, 0), (0, 1, 0), (0, 0, 1)])
        validate("and ^hear ~my =prayer.", "and hear my prayer.")
        with self.assertRaises(NotationError):
            validate("and ^^hear my prayer.", "and hear my prayer.")
        with self.assertRaises(NotationError):
            validate("and ^ hear my prayer.", "and hear my prayer.")

    def test_small_capitals_are_letters(self):
        from psalter.chant.notation import split_punctuation

        self.assertEqual(split_punctuation("Lᴏʀᴅ;"), ("", "Lᴏʀᴅ", ";"))
        self.assertEqual(dictionary.notate("the Lᴏʀᴅ’s house"), "the +Lᴏʀᴅ’s +house")


class BookPointingTests(SimpleTestCase):
    """Verses as the St. Bernard Psalter points them, for each kind of tone."""

    def test_book_tones_parse(self):
        for code, tone in TONES.items():
            if not tone.book:
                continue
            with self.subTest(tone=code):
                self.assertTrue(tone.mediation.tenor and tone.ending.tenor)
                # The first note after the reciting note is ticked in every book tone.
                self.assertTrue(tone.mediation.cadence[0].accent)
                self.assertTrue(tone.ending.cadence[0].accent)

    def test_psalm_23_in_tone_iv_4(self):
        sung, pointed = book_roles("The Lᴏʀᴅ ^is my ^shep/herd;", "B4.4", mediation=True)
        self.assertEqual(sung, [("is", "pointed"), ("my", "note"), ("shep", "pointed"), ("herd", "final")])
        self.assertEqual(pointed.warnings, [])
        # "my cup shall be full": "be" goes to the parentheses, not the accent.
        sung, pointed = book_roles("you have a/noint/ed my head with oil, ^and my cup ^shall be full.", "B4.4", False)
        self.assertEqual(
            sung,
            [
                ("and", "pointed"),
                ("my", "note"),
                ("cup", "note"),
                ("shall", "pointed"),
                ("be", "return"),
                ("full", "final"),
            ],
        )
        self.assertEqual(pointed.warnings, [])

    def test_a_short_mediation_drops_its_last_note(self):
        sung, pointed = book_roles("all the days ^of my ^life,", "B4.4", mediation=True)
        self.assertEqual(sung, [("of", "pointed"), ("my", "note"), ("life", "pointed")])
        self.assertEqual(pointed.warnings, [])

    def test_italic_takes_the_slur(self):
        sung, pointed = book_roles("have mer/cy up/on me, ^and hear ~my prayer.", "B1.1", mediation=False)
        self.assertEqual(sung, [("and", "pointed"), ("hear", "note"), ("my", "slur"), ("prayer", "final")])
        self.assertEqual(pointed.syllables[-2].notes, "gh")
        # Tone VI's slur has no tick; italic still goes there.
        sung, pointed = book_roles("he came fly/ing up/on the ^wings ~of ^the wind.", "B6", mediation=False)
        self.assertEqual(sung, [("wings", "pointed"), ("of", "slur"), ("the", "pointed"), ("wind", "final")])
        self.assertEqual(pointed.warnings, [])

    def test_bold_runs_on_to_the_parentheses(self):
        # II.1: the parenthesised note is ticked and may be left out.
        sung, pointed = book_roles("they shall fall and per/ish ^at your ^pres/^ence;", "B2.1", mediation=False)
        self.assertEqual(sung, [("at", "pointed"), ("your", "note"), ("pres", "pointed"), ("ence", "pointed")])
        sung, pointed = book_roles("I will speak of all your mar/^ve/lous ^works.", "B2.1", mediation=False)
        self.assertEqual(sung, [("ve", "pointed"), ("lous", "note"), ("works", "pointed")])
        self.assertEqual(pointed.warnings, [])

    def test_marks_that_do_not_fit_are_reported(self):
        _, pointed = book_roles("there/fore I can ^lack ^no/thing.", "B4.4", mediation=False)
        self.assertTrue(pointed.warnings)

    def test_without_marks_stress_is_used_and_flagged(self):
        sung, pointed = book_roles("there/fore I can +lack +noth/ing.", "B4.4", mediation=False)
        self.assertEqual(sung[-1], ("ing", "final"))
        self.assertIn("No marks from the book", pointed.warnings[0])

    def test_segments_show_bold_and_italic(self):
        from psalter.chant.pointing import point_verse

        tone = TONES["B1.1"]
        first, second = point_verse(
            "Hear me when I call, O God ^of my ^right/eous/ness;", "and ^hear ~my prayer.", tone
        )
        items = segments(second, tone.clef)
        self.assertIn("pointed", [i["r"] for i in items if i["t"] == "and"])
        self.assertIn("note", [i["r"] for i in items if i["t"] == "hear"])
        self.assertIn("slur", [i["r"] for i in items if i["t"] == "my"])
        self.assertEqual(describe(second), "| AND hear MY~ prayer.")


class SyllableTests(SimpleTestCase):
    def test_divisions(self):
        for word, expected in [
            ("shepherd", ["shep", "herd"]),
            ("therefore", ["there", "fore"]),
            ("righteousness", ["right", "eous", "ness"]),
            ("evil", ["e", "vil"]),
            ("Israel", ["Is", "ra", "el"]),
            ("every", ["ev", "ery"]),
            ("wickedness", ["wick", "ed", "ness"]),
            ("Blessèd", ["Bles", "sèd"]),
            ("blessed", ["blessed"]),
            ("fire", ["fire"]),
            ("peaceable", ["peace", "a", "ble"]),
            ("blasphemes", ["blas", "phemes"]),
        ]:
            with self.subTest(word=word):
                self.assertEqual(dictionary.syllabify(word), expected)


class BernardMatchTests(TestCase):
    def setUp(self):
        self.psalm = make_psalm()

    def words(self, text, tone="B4.4"):
        """Book words from text marked [bold] and <italic>, "*" after the first half."""
        import re

        from psalter.chant.bernard import BOLD, ITALIC, REGULAR, BookWord

        out = []
        for token in text.split():
            if token == "*":
                out[-1].half_break = True
                continue
            styles = []
            style = REGULAR
            for char in token:
                if char in "[<":
                    style = BOLD if char == "[" else ITALIC
                elif char in "]>":
                    style = REGULAR
                elif re.match(r"[^\W\d_]", char) and char not in "’'":
                    styles.append(style)
            out.append(BookWord(re.sub(r"[\[\]<>]", "", token), styles, tone, 54, "Day 4 Evening Prayer"))
        return out

    def test_marks_are_copied_onto_the_text(self):
        from psalter.chant.bernard import match_psalm

        book = self.words(
            "The Lord [is] my [shep]herd; * therefore [I] can lack [no]thing. "
            "He shall feed me [in] green [past]ures * and lead me forth beside the [wa]ters of [com]fort."
        )
        verses = list(self.psalm.psalmverse_set.order_by("number"))
        results = match_psalm(verses, book)
        self.assertEqual(results[0].first_half, "The Lord ^is my ^shep/herd;")
        self.assertEqual(results[0].second_half, "there/fore ^I can lack ^no/thing.")
        # The book's own division ("past|ures") wins over the dictionary's.
        self.assertEqual(results[1].first_half, "He shall feed me ^in green ^past/ures")
        self.assertEqual([r.issues for r in results], [[], []])
        self.assertEqual(results[0].tone, "B4.4")

    def test_differences_are_reported(self):
        from psalter.chant.bernard import match_psalm

        book = self.words(
            "The Lord [is] my [shep]herd; * so [I] shall lack [no]thing. "
            "He shall feed me [in] green [past]ures * and lead me forth beside the [wa]ters of [com]fort."
        )
        results = match_psalm(list(self.psalm.psalmverse_set.order_by("number")), book)
        self.assertTrue(any("so" in issue for issue in results[0].issues))
        self.assertEqual(results[1].issues, [])

    def test_a_drop_capital_joins_its_word(self):
        from psalter.chant.bernard import BookWord, _resolve_drop_caps

        words = [BookWord("T\x00he", ["r", "r"], "B4.4", 1), BookWord("I\x00call", ["r", "r", "r", "r"], "B4.4", 1)]
        resolved = _resolve_drop_caps(words, {"the", "i", "call"})
        self.assertEqual([w.text for w in resolved], ["The", "I", "call"])

    def test_import_stores_pointing_and_tones(self):
        from psalter.chant.service import import_book

        book = self.words(
            "The Lord [is] my [shep]herd; * therefore [I] can lack [no]thing. "
            "He shall feed me [in] green [past]ures * and lead me forth beside the [wa]ters of [com]fort."
        )
        import_book({23: book})
        self.psalm.refresh_from_db()
        self.assertEqual(self.psalm.chant_tone, "B4.4")
        pointing = PsalmVersePointing.objects.get(verse__psalm=self.psalm, verse__number=1)
        self.assertEqual(pointing.status, PsalmVersePointing.BOOK)
        self.assertEqual(pointing.source, PsalmVersePointing.SOURCE_BOOK)
        self.assertEqual((pointing.tone, pointing.book_page), ("B4.4", 54))
        chant = chant_for_verse(PsalmVerse.objects.select_related("pointing", "psalm").get(pk=pointing.verse_id))
        self.assertEqual(chant["tone"], "B4.4")
        # The AI leaves the book's pointing alone.
        self.assertEqual(point_psalm(self.psalm, use_ai=False), [])
        # An editor's approval survives a second import.
        pointing.status = PsalmVersePointing.APPROVED
        pointing.first_half_stress = "The Lord ^is ^my shep/herd;"
        pointing.save()
        results = import_book({23: book})
        self.assertTrue(results[23][0].skipped)
        pointing.refresh_from_db()
        self.assertEqual(pointing.first_half_stress, "The Lord ^is ^my shep/herd;")


class PointingProposalTests(TestCase):
    def setUp(self):
        from psalter.chant.service import import_book

        self.psalm = make_psalm()
        book = BernardMatchTests.words(
            None,
            "The Lord [is] my [shep]herd; * therefore [I] can lack [no]thing. "
            "He shall feed me [in] green [past]ures * and lead me forth beside the [wa]ters of [com]fort.",
        )
        import_book({23: book})

    def proposal(self, **changes):
        data = {
            "psalm": 23,
            "verse": 1,
            "first_half": "The Lord ^is my ^shep/herd;",
            "second_half": "there/fore ^I can ^lack ^no/thing.",
            "note": "A test.",
        }
        data.update(changes)
        return data

    def test_editor_gives_syllables_and_marks(self):
        response = self.client.get("/api/v1/psalms/23/verses/1/pointing")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tone"]["code"], "B4.4")
        self.assertTrue(data["tone"]["book"])
        self.assertEqual(
            [(s["t"], s["m"]) for s in data["second_half"]],
            [("there", ""), ("fore", ""), ("I", "^"), ("can", ""), ("lack", ""), ("no", "^"), ("thing.", "")],
        )
        self.assertEqual(self.client.get("/api/v1/psalms/23/verses/99/pointing").status_code, 404)

    def test_preview_sings_the_proposal(self):
        response = self.client.post("/api/v1/pointing/preview", self.proposal(), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["warnings"])
        response = self.client.post(
            "/api/v1/pointing/preview", self.proposal(second_half="other words"), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_proposals_are_stored_and_accepted(self):
        from django.contrib.admin.sites import site

        from psalter.admin import PointingProposalAdmin
        from psalter.models import PointingProposal

        same = self.proposal(second_half="there/fore ^I can lack ^no/thing.")
        self.assertEqual(
            self.client.post("/api/v1/pointing/proposals", same, content_type="application/json").status_code, 400
        )
        response = self.client.post("/api/v1/pointing/proposals", self.proposal(), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        proposal = PointingProposal.objects.get()
        self.assertEqual(proposal.previous_second_half, "there/fore ^I can lack ^no/thing.")
        self.assertEqual(proposal.tone, "B4.4")

        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(user)
        url = reverse("admin:psalter_pointingproposal_change", args=[proposal.pk])
        self.assertContains(self.client.get(url), "Now and proposed")
        admin = PointingProposalAdmin(PointingProposal, site)
        request = SimpleNamespace(user=user, _messages=SimpleNamespace(add=lambda *a, **k: None))
        admin.message_user = lambda *args, **kwargs: None
        admin.accept(request, PointingProposal.objects.all())
        pointing = PsalmVersePointing.objects.get(verse__psalm=self.psalm, verse__number=1)
        self.assertEqual(pointing.second_half_stress, "there/fore ^I can ^lack ^no/thing.")
        self.assertEqual((pointing.status, pointing.source), ("approved", "editor"))
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "accepted")


class PsalmSectionTests(TestCase):
    """Psalm 119's Hebrew letters head its sections, apart from the verse text."""

    LETTERED = {8: "Beth", 16: "Gimel"}

    def setUp(self):
        self.psalm = Psalm.objects.create(number=119, latin_title="Beati immaculati")
        for number in range(1, 18):
            letter = self.LETTERED.get(number)
            second = f" second half {number}." + (f" {letter}" if letter else "")
            PsalmVerse.objects.create(
                psalm=self.psalm,
                number=number,
                first_half=f" first half {number}",
                second_half=second,
                first_half_tle=f" thy first half {number}",
                second_half_tle=second.replace("second", "thy second"),
            )
        verse = PsalmVerse.objects.get(psalm=self.psalm, number=8)
        PsalmVersePointing.objects.create(
            verse=verse,
            first_half_stress="first ^half ~8",
            second_half_stress="sec/ond ^half ~8. Be/th",
            status=PsalmVersePointing.CHECK,
            source=PsalmVersePointing.SOURCE_BOOK,
            review_notes="The book has “nothing” where the text has “Beth”.",
        )

    def migrate(self):
        from importlib import import_module

        from django.apps import apps

        import_module("psalter.migrations.0011_psalmverse_section_heading").move_letters_to_headings(apps, None)

    def verse(self, number):
        return PsalmVerse.objects.select_related("psalm", "pointing").get(psalm=self.psalm, number=number)

    def test_migration_moves_letters_to_section_headings(self):
        self.migrate()
        self.migrate()  # and changes nothing the second time
        eight = self.verse(8)
        self.assertEqual(eight.second_half, " second half 8.")
        self.assertEqual(eight.second_half_tle, " thy second half 8.")
        self.assertEqual(self.verse(16).second_half, " second half 16.")
        headings = dict(
            PsalmVerse.objects.filter(psalm=self.psalm)
            .exclude(section_heading="")
            .values_list("number", "section_heading")
        )
        self.assertEqual(headings, {1: "Aleph", 9: "Beth", 17: "Gimel"})
        # The pointing drops the letter too, and the verse is the book's again.
        self.assertEqual(eight.pointing.second_half_stress, "sec/ond ^half ~8.")
        self.assertEqual(eight.pointing.status, PsalmVersePointing.BOOK)
        self.assertEqual(eight.pointing.review_notes, "")
        self.assertIsNotNone(chant_for_verse(eight))

    def test_office_lines_head_sections_and_say_letters_as_before(self):
        from office.api.views.index import spoken_psalm_sections
        from psalter.utils import get_psalms

        self.migrate()
        lines = get_psalms("119:1-8", api=True)
        sections = [line["content"] for line in lines if line.get("psalm_section")]
        self.assertEqual(sections, ["Aleph"])
        self.assertEqual(lines[2]["line_type"], "subheading")  # after the psalm's heading and title
        # The range ends before Beth; its audio still says the letter after verse 8.
        self.assertEqual(lines[-1]["content"], " second half 8.")
        self.assertEqual(lines[-1]["audio_suffix"], " Beth")

        lines = get_psalms("119:8-9", api=True, language_style="traditional")
        contents = [line["content"] for line in lines]
        self.assertLess(contents.index(" thy second half 8."), contents.index("Beth"))
        self.assertLess(contents.index("Beth"), contents.index(" thy first half 9 *"))
        spoken = spoken_psalm_sections([{"name": "Psalms", "lines": lines}])[0]["lines"]
        self.assertNotIn("Beth", [line["content"] for line in spoken])
        self.assertIn(" thy second half 8. Beth", [line["content"] for line in spoken])

        html = get_psalms("119:8-9")
        self.assertLess(html.index("second half 8."), html.index("<h4 class='psalm-section'>Beth</h4>"))

    def test_other_languages_have_no_section_headings(self):
        self.migrate()
        PsalmVerse.objects.filter(psalm=self.psalm).update(first_half_spanish="primera", second_half_spanish="segunda")
        lines = psalm_api_lines(
            "119", list(PsalmVerse.objects.filter(psalm=self.psalm).order_by("number")), display_language="spanish"
        )
        self.assertFalse(any(line.get("psalm_section") or line.get("audio_suffix") for line in lines))
        self.assertTrue(lines)

    def test_psalm_api_gives_section_headings(self):
        self.migrate()
        verses = self.client.get("/api/v1/psalms/119/").json()["verses"]
        self.assertEqual(verses[8]["section_heading"], "Beth")
        self.assertEqual(verses[7]["section_heading"], "")
        self.assertEqual(verses[7]["second_half"], " second half 8.")

    def test_split_trailing_letter(self):
        from psalter.sections import section_letter, split_trailing_letter

        self.assertEqual(split_trailing_letter(" and walk in the law. Beth"), (" and walk in the law.", "Beth"))
        self.assertEqual(split_trailing_letter("Behold, He"), ("Behold,", "He"))
        self.assertEqual(split_trailing_letter("for ever."), ("for ever.", None))
        self.assertEqual([section_letter(n) for n in (1, 8, 9, 169, 177)], ["Aleph", None, "Beth", "Taw", None])


class CantaiFailureTests(SimpleTestCase):
    def test_a_failed_cantai_render_is_caught(self):
        import tempfile
        import time
        from pathlib import Path

        from psalter.management.commands.record_chant import cantai_failure

        with tempfile.TemporaryDirectory() as directory:
            logs = Path(directory)
            started = time.time() - 1
            # No sign of Cantai: MuseScore fell back to its basic sound.
            (logs / "MuseScore_1.log").write_text("INFO | MuseSampler successfully inited\n")
            self.assertIn("basic sound", cantai_failure(started, logs))
            (logs / "MuseScore_1.log").write_text(
                "INFO | MuseSampler successfully inited\n"
                "INFO | MuseSamplerResolver::init | >>> Cantai convert cache lookup for request 5 (hit: true)\n"
            )
            self.assertEqual(cantai_failure(started, logs), "")
            (logs / "MuseScore_2.log").write_text(
                "ERROR | MuseSamplerResolver::init | >>> Cantai render failed: The socket was closed due to a timeout\n"
            )
            self.assertIn("Cantai render failed", cantai_failure(started, logs))
            # Logs from before the render don't count, so Cantai's earlier
            # singing doesn't vouch for a later render.
            self.assertIn("basic sound", cantai_failure(time.time() + 60, logs))

    def test_recordings_are_brought_to_a_standard_loudness(self):
        import shutil
        import subprocess
        import tempfile
        from pathlib import Path

        from psalter.management.commands.record_chant import LOUDNESS, encode_mp3

        if not shutil.which("ffmpeg"):
            self.skipTest("ffmpeg is not installed")
        with tempfile.TemporaryDirectory() as directory:
            wav = Path(directory) / "quiet.wav"
            mp3 = Path(directory) / "quiet.mp3"
            # Ten seconds of a quiet tone, like a Cantai render.
            subprocess.run(
                [
                    "ffmpeg",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=220:duration=10",
                    "-af",
                    "volume=-30dB",
                    str(wav),
                ],
                check=True,
            )
            encode_mp3(wav, mp3)
            report = subprocess.run(
                ["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3), "-af", "ebur128", "-f", "null", "-"],
                capture_output=True,
                text=True,
                check=True,
            ).stderr
            integrated = float(report.rsplit("I:", 1)[1].split("LUFS")[0])
            self.assertAlmostEqual(integrated, LOUDNESS, delta=1)
            rate = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", str(mp3)],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(rate, "44100")
