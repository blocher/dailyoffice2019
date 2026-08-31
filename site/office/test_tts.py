import base64
import os
import tempfile
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from office.api.views.tts import ElevenLabsTTSProvider


class ElevenLabsTTSProviderTests(SimpleTestCase):
    @override_settings(
        ELEVENLABS_TTS_VOICE_LEADER="leader-id",
        ELEVENLABS_TTS_VOICE_CONGREGATION="people-id",
        ELEVENLABS_TTS_VOICES_READER=("reader-one", "reader-two"),
    )
    def test_roles_share_configured_voices_and_reader_is_selected_from_list(self):
        provider = ElevenLabsTTSProvider()

        self.assertEqual(provider.voice_for_line_type("leader"), "leader-id")
        self.assertEqual(provider.voice_for_line_type("leader_dialogue"), "leader-id")
        self.assertEqual(provider.voice_for_line_type("congregation"), "people-id")
        self.assertEqual(provider.voice_for_line_type("congregation_dialogue"), "people-id")
        with patch("office.api.views.tts.random.choice", return_value="reader-two") as choice:
            self.assertEqual(provider.voice_for_line_type("reader"), "reader-two")
            choice.assert_called_once_with(("reader-one", "reader-two"))

    @override_settings(
        ELEVENLABS_API_KEY="test-key",
        ELEVENLABS_TTS_MODEL="eleven_v3",
        ELEVENLABS_TTS_SPEED=0.9,
        ELEVENLABS_TTS_MAX_RETRIES=0,
    )
    @patch("office.api.views.tts.requests.post")
    def test_synthesize_writes_audio_and_returns_word_alignment(self, post):
        response = MagicMock()
        response.json.return_value = {
            "audio_base64": base64.b64encode(b"mp3-data").decode(),
            "alignment": {
                "characters": list("Peace be."),
                "character_start_times_seconds": [index / 10 for index in range(9)],
                "character_end_times_seconds": [(index + 1) / 10 for index in range(9)],
            },
        }
        post.return_value = response

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "clip.mp3")
            words = ElevenLabsTTSProvider().synthesize("voice-id", "Peace be.", path)

            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), b"mp3-data")

        self.assertEqual(
            words,
            [
                {
                    "word": "Peace",
                    "start_time": 0.0,
                    "end_time": 0.5,
                    "char_start": 0,
                    "char_end": 5,
                },
                {
                    "word": "be",
                    "start_time": 0.6,
                    "end_time": 0.8,
                    "char_start": 6,
                    "char_end": 8,
                },
            ],
        )
        post.assert_called_once()
        request = post.call_args
        self.assertEqual(request.kwargs["json"]["model_id"], "eleven_v3")
        self.assertEqual(request.kwargs["json"]["voice_settings"]["speed"], 0.9)
        self.assertEqual(request.kwargs["params"]["output_format"], "mp3_44100_128")
