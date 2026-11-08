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
        self.assertEqual(sung[-1]["d"], [2])

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
        self.assertContains(self.client.get(url), "Syllables and stresses")

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
        # A rest of two pulses at the asterisk.
        first_half_end = notes[5].onset + notes[5].pulses
        self.assertEqual(notes[6].onset, first_half_end + 2)
        self.assertEqual(length, notes[-1].onset + notes[-1].pulses)

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
            xml = Path(directory) / "psalm.musicxml"
            call_command("export_chant", "23", "--format", "musicxml", "--out", str(xml), stdout=StringIO())
            document = minidom.parse(str(xml))
            lyrics = [t.firstChild.data for t in document.getElementsByTagName("text")]
            self.assertEqual(lyrics[:6], ["The", "Lord", "is", "my", "shep", "herd"])

    def test_command_needs_a_pointed_psalm(self):
        Psalm.objects.create(number=24)
        with self.assertRaises(CommandError):
            call_command("export_chant", "24", stdout=StringIO())
