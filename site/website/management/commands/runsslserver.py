import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

# Kept beside the project (and gitignored) rather than in /tmp, so the certificate survives reboots.
CERT_DIR = Path(settings.BASE_DIR) / ".dev-certs"
MKCERT_CERT = CERT_DIR / "localhost.crt"
MKCERT_KEY = CERT_DIR / "localhost.key"
SELF_SIGNED_CERT = Path("/tmp/cert.crt")


class Command(BaseCommand):
    help = "Run server with SSL, using a browser-trusted mkcert certificate when mkcert is installed"

    def add_arguments(self, parser):
        parser.add_argument(
            "addrport", nargs="?", help="Optional port number, or ipaddr:port (default 127.0.0.1:8000)"
        )

    def handle(self, *args, **options):
        addrport = [options["addrport"]] if options.get("addrport") else []
        cert, key = self.certificate()
        call_command("runserver_plus", *addrport, cert_path=str(cert), key_file_path=key and str(key))

    def certificate(self):
        """Use a certificate signed by mkcert's local CA, which browsers trust once `mkcert -install` has run.

        Without mkcert, fall back to runserver_plus's self-signed certificate, which each browser must be told to accept.
        Returns (cert, key); a key of None lets runserver_plus derive it from the cert path.
        """
        mkcert = shutil.which("mkcert")
        if not mkcert:
            self.stderr.write(
                "mkcert not found, so serving a self-signed certificate your browser will warn about. "
                "Install it once to fix that: brew install mkcert && mkcert -install"
            )
            return SELF_SIGNED_CERT, None
        if not (MKCERT_CERT.exists() and MKCERT_KEY.exists()):
            CERT_DIR.mkdir(exist_ok=True)
            subprocess.run(
                [mkcert, "-cert-file", MKCERT_CERT, "-key-file", MKCERT_KEY, "localhost", "127.0.0.1", "::1"],
                check=True,
            )
        return MKCERT_CERT, MKCERT_KEY
