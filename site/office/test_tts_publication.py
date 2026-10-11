"""Synthetic filesystem regressions; provider requests never leave the process."""

import base64
import errno
import os
import stat
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from office.api.views.tts import ElevenLabsTTSProvider, FishAudioTTSProvider


class PublicationTests:
    def request(self, *args, **kwargs):
        audio = kwargs["json"]["text"].encode()
        response = MagicMock()
        response.json.return_value = {"audio_base64": base64.b64encode(audio).decode()}
        response.iter_content.return_value = [audio[:2], b"", audio[2:]]
        response.__enter__.return_value = response
        return response

    def synthesize(self, text, path):
        raise NotImplementedError

    def concurrent_calls(self, directory, independent=False, fail_second=False):
        barrier = threading.Barrier(2, timeout=5)
        published = threading.Event()
        real_replace = os.replace
        lock = threading.Lock()
        sources = []

        def replace(source, target):
            with lock:
                position = len(sources)
                sources.append(source)
            barrier.wait()  # Both complete writes precede either rename.
            if position == 0:
                try:
                    return real_replace(source, target)
                finally:
                    published.set()
            self.assertTrue(published.wait(5))
            if fail_second:
                raise PermissionError(errno.EACCES, "synthetic publication failure")
            return real_replace(source, target)

        paths = [
            os.path.join(directory, "clip.mp3"),
            os.path.join(directory, "other.mp3" if independent else "clip.mp3"),
        ]
        with patch("office.api.views.tts.os.replace", side_effect=replace), ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.synthesize, text, path) for text, path in zip(("first", "second"), paths)]
            errors = [future.exception(timeout=10) for future in futures]
        return paths, sources, errors

    @patch("office.api.views.tts.requests.post")
    def test_concurrent_same_clip_publishes_complete_audio(self, post):
        post.side_effect = self.request
        with tempfile.TemporaryDirectory() as directory:
            paths, sources, errors = self.concurrent_calls(directory)
            self.assertEqual(errors, [None, None])
            self.assertEqual(len(set(sources)), 2)
            self.assertTrue(all(os.path.dirname(source) == directory for source in sources))
            with open(paths[0], "rb") as handle:
                self.assertIn(handle.read(), (b"first", b"second"))
            self.assertEqual(os.listdir(directory), ["clip.mp3"])

    @patch("office.api.views.tts.requests.post")
    def test_independent_paths_publish_independently(self, post):
        post.side_effect = self.request
        with tempfile.TemporaryDirectory() as directory:
            paths, _, errors = self.concurrent_calls(directory, independent=True)
            self.assertEqual(errors, [None, None])
            for path, audio in zip(paths, (b"first", b"second")):
                with open(path, "rb") as handle:
                    self.assertEqual(handle.read(), audio)
            self.assertEqual(sorted(os.listdir(directory)), ["clip.mp3", "other.mp3"])

    @patch("office.api.views.tts.requests.post")
    def test_failed_concurrent_writer_preserves_successful_publication(self, post):
        post.side_effect = self.request
        with tempfile.TemporaryDirectory() as directory:
            paths, _, errors = self.concurrent_calls(directory, fail_second=True)
            self.assertEqual(sum(error is None for error in errors), 1)
            self.assertEqual(sum(isinstance(error, PermissionError) for error in errors), 1)
            with open(paths[0], "rb") as handle:
                self.assertIn(handle.read(), (b"first", b"second"))
            self.assertEqual(os.listdir(directory), ["clip.mp3"])

    @patch("office.api.views.tts.requests.post")
    def test_success_is_atomic_and_leaves_unrelated_temp_alone(self, post):
        post.side_effect = self.request
        real_replace = os.replace
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "clip.mp3")
            with open(path, "wb") as handle:
                handle.write(b"cached")
            with open(path + ".part", "wb") as handle:
                handle.write(b"another writer")

            def replace(source, target):
                with open(target, "rb") as handle:
                    self.assertEqual(handle.read(), b"cached")
                with open(source, "rb") as handle:
                    self.assertEqual(handle.read(), b"fresh")
                self.assertNotEqual(source, path + ".part")
                return real_replace(source, target)

            with patch("office.api.views.tts.os.replace", side_effect=replace):
                self.synthesize("fresh", path)
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), b"fresh")
            with open(path + ".part", "rb") as handle:
                self.assertEqual(handle.read(), b"another writer")
            self.assertEqual(sorted(os.listdir(directory)), ["clip.mp3", "clip.mp3.part"])

    @patch("office.api.views.tts.requests.post")
    def test_replace_failure_or_cancellation_cleans_only_own_temp(self, post):
        post.side_effect = self.request
        for error in (
            FileNotFoundError(errno.ENOENT, "synthetic"),
            OSError(errno.ENOSPC, "synthetic"),
            PermissionError(errno.EACCES, "synthetic"),
            KeyboardInterrupt(),
        ):
            for cached in (False, True):
                with (
                    self.subTest(error=type(error).__name__, cached=cached),
                    tempfile.TemporaryDirectory() as directory,
                ):
                    path = os.path.join(directory, "clip.mp3")
                    if cached:
                        with open(path, "wb") as handle:
                            handle.write(b"cached")
                    with open(path + ".part", "wb") as handle:
                        handle.write(b"another writer")
                    with patch("office.api.views.tts.os.replace", side_effect=error):
                        with self.assertRaises(type(error)) as caught:
                            self.synthesize("fresh", path)
                    self.assertIs(caught.exception, error)
                    if cached:
                        with open(path, "rb") as handle:
                            self.assertEqual(handle.read(), b"cached")
                    else:
                        self.assertFalse(os.path.exists(path))
                    with open(path + ".part", "rb") as handle:
                        self.assertEqual(handle.read(), b"another writer")
                    self.assertEqual(
                        sorted(os.listdir(directory)), ["clip.mp3", "clip.mp3.part"] if cached else ["clip.mp3.part"]
                    )

    @patch("office.api.views.tts.requests.post")
    def test_new_output_keeps_normal_file_permissions(self, post):
        post.side_effect = self.request
        with tempfile.TemporaryDirectory() as directory:
            reference = os.path.join(directory, "reference.mp3")
            path = os.path.join(directory, "clip.mp3")
            with open(reference, "wb") as handle:
                handle.write(b"reference")
            self.synthesize("fresh", path)
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), stat.S_IMODE(os.stat(reference).st_mode))

    @patch("office.api.views.tts.requests.post")
    def test_temp_name_collision_never_deletes_another_writers_file(self, post):
        post.side_effect = self.request
        with tempfile.TemporaryDirectory() as directory:
            temporary = os.path.join(directory, "tts-synthetic.part")
            with open(temporary, "wb") as handle:
                handle.write(b"another writer")
            with patch("office.api.views.tts.uuid.uuid4", return_value=MagicMock(hex="synthetic")):
                with self.assertRaises(FileExistsError):
                    self.synthesize("fresh", os.path.join(directory, "clip.mp3"))
            with open(temporary, "rb") as handle:
                self.assertEqual(handle.read(), b"another writer")
            self.assertEqual(os.listdir(directory), ["tts-synthetic.part"])

    @patch("office.api.views.tts.requests.post")
    def test_partial_write_failure_and_cancellation_clean_own_temp(self, post):
        post.side_effect = self.request
        real_open = open
        for error in (OSError(errno.ENOSPC, "synthetic"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "clip.mp3")
                with open(path, "wb") as handle:
                    handle.write(b"cached")

                def temporary(*args, **kwargs):
                    handle = real_open(*args, **kwargs)
                    write = handle.write

                    def fail(audio):
                        write(audio[:1])
                        raise error

                    handle.write = fail
                    return handle

                with patch("office.api.views.tts.open", side_effect=temporary):
                    with self.assertRaises(type(error)):
                        self.synthesize("fresh", path)
                with open(path, "rb") as handle:
                    self.assertEqual(handle.read(), b"cached")
                self.assertEqual(os.listdir(directory), ["clip.mp3"])


@override_settings(
    ELEVENLABS_API_KEY="synthetic-key",
    ELEVENLABS_TTS_MAX_RETRIES=0,
    ELEVENLABS_TTS_MODEL="eleven_multilingual_v2",
    ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="",
)
class ElevenLabsPublicationTests(PublicationTests, SimpleTestCase):
    def synthesize(self, text, path):
        return ElevenLabsTTSProvider().synthesize("synthetic-voice", text, path)


class FishPublicationTests(PublicationTests, SimpleTestCase):
    def synthesize(self, text, path):
        return FishAudioTTSProvider()._synthesize_once({"text": text}, {}, path)
