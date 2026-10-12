import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from website.management.commands import runsslserver


class RunSSLServerTests(SimpleTestCase):
    def setUp(self):
        self.cert_dir = Path(tempfile.mkdtemp())
        for name, value in {
            "CERT_DIR": self.cert_dir,
            "MKCERT_CERT": self.cert_dir / "localhost.crt",
            "MKCERT_KEY": self.cert_dir / "localhost.key",
        }.items():
            patcher = patch.object(runsslserver, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    @patch.object(runsslserver.subprocess, "run")
    @patch.object(runsslserver.shutil, "which", return_value="/usr/local/bin/mkcert")
    @patch.object(runsslserver, "call_command")
    def test_generates_and_serves_mkcert_certificate(self, serve, which, run):
        call_command("runsslserver", "127.0.0.1:8006")

        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][-3:], ["localhost", "127.0.0.1", "::1"])
        serve.assert_called_once_with(
            "runserver_plus",
            "127.0.0.1:8006",
            cert_path=str(self.cert_dir / "localhost.crt"),
            key_file_path=str(self.cert_dir / "localhost.key"),
        )

    @patch.object(runsslserver.subprocess, "run")
    @patch.object(runsslserver.shutil, "which", return_value="/usr/local/bin/mkcert")
    @patch.object(runsslserver, "call_command")
    def test_reuses_existing_mkcert_certificate(self, serve, which, run):
        (self.cert_dir / "localhost.crt").touch()
        (self.cert_dir / "localhost.key").touch()

        call_command("runsslserver")

        run.assert_not_called()
        self.assertEqual(serve.call_args.args, ("runserver_plus",))

    @patch.object(runsslserver.shutil, "which", return_value=None)
    @patch.object(runsslserver, "call_command")
    def test_falls_back_to_self_signed_without_mkcert(self, serve, which):
        call_command("runsslserver", stderr=StringIO())

        serve.assert_called_once_with("runserver_plus", cert_path="/tmp/cert.crt", key_file_path=None)
