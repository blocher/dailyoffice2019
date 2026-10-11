from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from churchcal.audio_streaming import audio_file_response


class AudioStreamingTests(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "provider").mkdir()
        (self.root / "provider/track.mp3").write_bytes(b"0123456789")

    def response(self, header="", filename="provider/track.mp3", **kwargs):
        response = audio_file_response(self.root, filename, header, **kwargs)
        self.addCleanup(response.close)
        return response

    def test_full_file_advertises_ranges(self):
        response = self.response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Length"], "10")
        self.assertEqual(b"".join(response.streaming_content), b"0123456789")

    def test_partial_content_windows(self):
        for header, expected_range, expected in [
            ("bytes=2-5", "bytes 2-5/10", b"2345"),
            ("bytes=7-", "bytes 7-9/10", b"789"),
            ("bytes=-3", "bytes 7-9/10", b"789"),
            ("bytes=0-0", "bytes 0-0/10", b"0"),
            ("bytes=8-999", "bytes 8-9/10", b"89"),
            ("bytes=-100", "bytes 0-9/10", b"0123456789"),
        ]:
            with self.subTest(header=header):
                response = self.response(header)
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response["Content-Range"], expected_range)
                self.assertEqual(int(response["Content-Length"]), len(expected))
                self.assertEqual(b"".join(response.streaming_content), expected)

    def test_unsatisfiable_ranges(self):
        for header in ["bytes=10-", "bytes=7-2", "bytes=-0"]:
            with self.subTest(header=header):
                response = self.response(header)
                self.assertEqual(response.status_code, 416)
                self.assertEqual(response["Content-Range"], "bytes */10")

    def test_extremely_large_offsets_are_bounded_without_integer_errors(self):
        huge = "9" * 5000
        self.assertEqual(self.response(f"bytes={huge}-").status_code, 416)
        response = self.response(f"bytes=2-{huge}")
        self.assertEqual(b"".join(response.streaming_content), b"23456789")
        response = self.response(f"bytes=-{huge}")
        self.assertEqual(b"".join(response.streaming_content), b"0123456789")
        response = self.response(f"bytes={'0' * 5000}2-3")
        self.assertEqual(b"".join(response.streaming_content), b"23")

    def test_unsupported_ranges_and_if_range_serve_full_file(self):
        for header in ["items=0-1", "bytes=nope", "bytes=0-1,4-5", "bytes=--1"]:
            self.assertEqual(self.response(header).status_code, 200)
        self.assertEqual(self.response("bytes=0-1", if_range='"old-version"').status_code, 200)

    def test_missing_empty_and_outside_files_are_not_served(self):
        (self.root / "empty.mp3").touch()
        for filename in ["missing.mp3", "empty.mp3", "../outside.mp3", "/etc/passwd"]:
            with self.subTest(filename=filename):
                self.assertEqual(self.response(filename=filename).status_code, 404)
        (self.root / "escape.mp3").symlink_to("/etc/passwd")
        self.assertEqual(self.response(filename="escape.mp3").status_code, 404)

    def test_closing_unconsumed_response_closes_source(self):
        response = self.response("bytes=2-5")
        source_close = response._resource_closers[-1]
        response.close()
        self.assertTrue(source_close.__self__.closed)
