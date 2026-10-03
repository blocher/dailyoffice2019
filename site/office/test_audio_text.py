from unittest import TestCase

from office.audio_text import expand_spoken_numbers, reading_text


def normalize_audio_text(text):
    return expand_spoken_numbers(reading_text(text))


class AudioTextTests(TestCase):
    def test_quantities_are_expanded_without_losing_digits(self):
        examples = {
            "35,000 men": "thirty-five thousand men",
            "35000 men": "thirty-five thousand men",
            "150 people and 151 people": "one hundred and fifty people and one hundred and fifty-one people",
            "There were 12 baskets and 144000 people.": "There were twelve baskets and one hundred and forty-four thousand people.",
            "0, 7, 1,234,567.": "zero, seven, one million, two hundred and thirty-four thousand, five hundred and sixty-seven.",
            "The 21st day": "The twenty-first day",
            "3.50 measures": "three point five zero measures",
        }
        for text, expected in examples.items():
            with self.subTest(text=text):
                self.assertEqual(normalize_audio_text(text), expected)

    def test_only_explicit_verse_and_chapter_labels_are_removed(self):
        html = (
            '<span class="chapternum">4 </span><sup class="versenum">2 </sup>35,000 men. '
            '<sup class="verse-num">3</sup>12 baskets. '
            '<b class="chapter-num">5</b><span class="verse-number">1</span>7 days.'
        )
        self.assertEqual(normalize_audio_text(html), "thirty-five thousand men. twelve baskets. seven days.")
        self.assertEqual(normalize_audio_text("<sup>12</sup> baskets"), "twelve baskets")

    def test_dates_references_and_identifiers_are_not_reinterpreted_as_quantities(self):
        text = "John 3:16-18, Psalm 119:1–8; 2026-09-30, 9/30/2026; BCP2019"
        self.assertEqual(normalize_audio_text(text), text)

    def test_existing_words_and_divine_names(self):
        self.assertEqual(normalize_audio_text("<b>LORD</b>  be with you. Lᴏʀᴅ"), "LORD be with you. Lᴏʀᴅ")
        self.assertEqual(normalize_audio_text(None), "")

    def test_normalization_is_idempotent_for_cache_keys(self):
        text = normalize_audio_text("35,000 men and 3.50 measures")
        self.assertEqual(normalize_audio_text(text), text)


class MasterAudioIntegrationTests(TestCase):
    def test_pronunciation_overrides_run_before_number_expansion(self):
        from unittest.mock import patch

        from office.api.views.index import GenericDailyOfficeSerializer

        with patch("office.models.PronunciationOverride.apply", return_value="12 baskets * remain") as override:
            result = GenericDailyOfficeSerializer.normalize_tts_text("a dozen baskets * remain")
        override.assert_called_once_with("a dozen baskets * remain")
        self.assertEqual(result, "twelve baskets remain")

    def test_paragraph_grouping_and_display_are_preserved(self):
        import re
        from unittest.mock import patch

        from office.api.views.index import GenericDailyOfficeSerializer

        html = '<p><span class="chapternum">4 </span><sup class="verse-num">2</sup>35,000 men. 3.5 measures.</p>'
        with patch.object(
            GenericDailyOfficeSerializer,
            "get_or_create_clip",
            return_value=("https://example.com/uploads/abc123.mp3", "/uploads/abc123.mp3"),
        ) as generate:
            rendered = GenericDailyOfficeSerializer.handle_html(
                html, html=True, no_generate=True, id="reading_original"
            )
        generate.assert_called_once_with("35,000 men. 3.5 measures.", "reader", kind="reader", no_generate=True)
        self.assertEqual(re.sub(r"<span data-line-id='[^']*'></span>", "", rendered), html)

    def test_clip_synthesis_receives_words_and_cache_key_changes(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from django.test import override_settings

        from office.api.views.index import GenericDailyOfficeSerializer

        serializer = GenericDailyOfficeSerializer
        with (
            tempfile.TemporaryDirectory() as media,
            override_settings(MEDIA_ROOT=media),
            patch("office.models.PronunciationOverride.apply", side_effect=lambda text: text),
            patch.object(serializer, "record_audio_clip"),
            patch.object(
                serializer, "synthesize_speech", side_effect=lambda voice, text, path: Path(path).write_bytes(b"mp3")
            ) as synthesize,
        ):
            url, path = serializer.get_or_create_clip("35,000 men", "reader")
            self.assertTrue(url)
            self.assertTrue(path)
            self.assertEqual(synthesize.call_args.args[1], "thirty-five thousand men")
            voice = synthesize.call_args.args[0]
            self.assertNotEqual(
                serializer.tts_clip_key(voice, "35,000 men"),
                serializer.tts_clip_key(voice, "thirty-five thousand men"),
            )
            self.assertEqual(serializer.get_or_create_clip("35,000 men", "reader"), (url, path))
            self.assertEqual(synthesize.call_count, 1)
