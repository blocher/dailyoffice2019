import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from office.gemini_alignment import align_clip, interpolate_short_gaps, match_words
from office.api.views import index
from office.api.views.tts import GeminiTTSProvider


def annotation(word, start, end):
    return {"type": "word_info", "text": word, "start_offset": f"{start}s", "end_offset": f"{end}s"}


@override_settings(GEMINI_TTS_ALIGNMENT=True, GEMINI_API_KEY="test")
class GeminiAlignmentTests(SimpleTestCase):
    def test_original_text_offsets_and_repetitions(self):
        text = "O Lord, our Lord. Amen."
        words = match_words(
            text, [annotation(w, i, i + 0.5) for i, w in enumerate(["Oh", "Lord,", "our", "Lord.", "Amen."])], 5
        )
        self.assertEqual([w["word"] for w in words], ["O", "Lord", "our", "Lord", "Amen"])
        self.assertEqual([text[w["char_start"] : w["char_end"]] for w in words], [w["word"] for w in words])
        self.assertEqual(words[3]["start_time"], 3)

    def test_short_gaps_preserve_anchors_and_weight_estimates(self):
        text = "Lord guide us this day"
        anchors = [
            {"word": "Lord", "char_start": 0, "char_end": 4, "start_time": 0, "end_time": 0.5},
            {"word": "this", "char_start": 14, "char_end": 18, "start_time": 1.2, "end_time": 1.5},
        ]
        words = interpolate_short_gaps(text, anchors)
        self.assertEqual([w["word"] for w in words], ["Lord", "guide", "us", "this"])
        self.assertEqual(words[0], anchors[0])
        self.assertEqual(words[-1], anchors[-1])
        self.assertAlmostEqual(words[1]["end_time"], 1.0)
        self.assertAlmostEqual(words[2]["start_time"], 1.0)
        self.assertTrue(words[1]["estimated"])
        self.assertEqual(interpolate_short_gaps(text, words), words)
        self.assertEqual([text[w["char_start"] : w["char_end"]] for w in words], [w["word"] for w in words])

    def test_does_not_bridge_long_gaps_punctuation_or_many_words(self):
        for text, gap in [
            ("Lord guide us", 2),
            ("Lord, guide us", 0.4),
            ("Lord guide and keep us", 1),
            ("Lord guide us", 0),
            ("Lord guide us", 0.01),
        ]:
            anchors = [
                {"word": "Lord", "char_start": 0, "char_end": 4, "start_time": 0, "end_time": 0.5},
                {
                    "word": "us",
                    "char_start": len(text) - 2,
                    "char_end": len(text),
                    "start_time": 0.5 + gap,
                    "end_time": 1 + gap,
                },
            ]
            with self.subTest(text=text, gap=gap):
                self.assertEqual(interpolate_short_gaps(text, anchors), anchors)

    def test_cached_timings_fill_without_transcription(self):
        text = "Lord guide us"
        anchors = [
            {"word": "Lord", "char_start": 0, "char_end": 4, "start_time": 0, "end_time": 0.5},
            {"word": "us", "char_start": 11, "char_end": 13, "start_time": 0.9, "end_time": 1.2},
        ]
        with (
            patch("office.models.AudioClip.objects") as clips,
            patch.object(index.GenericDailyOfficeSerializer, "normalize_tts_text", side_effect=lambda t: t),
            patch.object(index, "TTS_PROVIDER", GeminiTTSProvider()),
            patch("office.gemini_alignment.align_clip") as align,
        ):
            clips.filter.return_value.values_list.return_value.first.return_value = anchors
            words = index.GenericDailyOfficeSerializer.get_clip_word_timing("/uploads/gemini/test.mp3", text)
            self.assertEqual([w["word"] for w in words], ["Lord", "guide", "us"])
            align.assert_not_called()

    def test_zero_duration_words_remain_valid_line_anchors(self):
        words = match_words(
            "O Lord Amen", [annotation("O", 0, 0.2), annotation("Lord", 0.2, 0.2), annotation("Amen", 0.2, 0.8)], 1
        )
        self.assertEqual([word["word"] for word in words], ["O", "Lord", "Amen"])
        self.assertEqual(words[1]["start_time"], words[1]["end_time"])

    def test_rejects_mismatch_and_invalid_times(self):
        for annotations in [
            [annotation("Goodbye", 0, 1)],
            [annotation("Amen", -1, 1)],
            [annotation("Amen", 1, 10)],
            [annotation("Amen", "nan", 1)],
        ]:
            with self.subTest(annotations=annotations), self.assertRaises(ValueError):
                match_words("Amen", annotations, 3)

    def test_cache_failure_cooldown_and_audio_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clip.mp3"
            original = (Path(__file__).parent / "audio_assets/prayer_chime.mp3").read_bytes()
            path.write_bytes(original)
            provider = Mock()
            provider._request.side_effect = RuntimeError("secret upstream error")
            self.assertEqual(align_clip(provider, "Amen", str(path)), [])
            self.assertEqual(align_clip(provider, "Amen", str(path)), [])
            self.assertEqual(provider._request.call_count, 1)
            cache = Path(str(path) + ".gemini-alignment.json")
            data = json.loads(cache.read_text())
            self.assertNotIn("secret", cache.read_text())
            data["retry_after"] = 0
            cache.write_text(json.dumps(data))
            provider._request.side_effect = None
            provider._request.return_value.json.return_value = {
                "steps": [
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "annotations": [annotation("Amen.", 0.1, 0.8)]}],
                    }
                ]
            }
            self.assertEqual(len(align_clip(provider, "Amen.", str(path))), 1)
            self.assertEqual(len(align_clip(provider, "Amen.", str(path))), 1)
            self.assertEqual(provider._request.call_count, 2)
            self.assertEqual(path.read_bytes(), original)

    def test_existing_clip_backfills_without_synthesis(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch.object(index, "TTS_PROVIDER", GeminiTTSProvider()),
            patch.object(index.GenericDailyOfficeSerializer, "normalize_tts_text", side_effect=lambda t: t),
            patch.object(index.GenericDailyOfficeSerializer, "find_reusable_reader", return_value=None),
            patch.object(index.GenericDailyOfficeSerializer, "get_clip_word_timing", return_value=[]),
            patch.object(index.GenericDailyOfficeSerializer, "record_audio_clip") as record,
            patch.object(index.GenericDailyOfficeSerializer, "synthesize_speech") as synth,
            patch("office.gemini_alignment.align_clip", return_value=[{"word": "Amen"}]) as align,
        ):
            voice = index.TTS_PROVIDER.voice_for_text("leader", "Amen")
            key = index.GenericDailyOfficeSerializer.tts_clip_key(voice, "Amen")
            path = Path(directory) / "gemini" / f"{key}.mp3"
            path.parent.mkdir()
            path.write_bytes(b"existing")
            index.GenericDailyOfficeSerializer.get_or_create_clip("Amen", "leader")
            align.assert_called_once()
            synth.assert_not_called()
            self.assertEqual(record.call_args.args[-1], [{"word": "Amen"}])
