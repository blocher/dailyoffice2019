"""Run a private loopback audition tool: python manage.py voice_auditions."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand

from office.voice_auditions import AuditionStore


def make_handler(store, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def send(self, status, body, content_type="application/json"):
            if not isinstance(body, bytes):
                body = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(body)

        def valid_host(self):
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {"error": "Use the loopback URL printed in your terminal."})
            path = urlparse(self.path).path
            if path == "/":
                template = Path(__file__).resolve().parents[2] / "templates/office/voice_auditions.html"
                html = template.read_text().replace("__SESSION_TOKEN__", token)
                return self.send(200, html.encode(), "text/html; charset=utf-8")
            if path == "/voice-auditions.js":
                script = Path(__file__).resolve().parents[2] / "templates/office/voice_auditions.js"
                return self.send(200, script.read_bytes(), "text/javascript; charset=utf-8")
            if path == "/api/state":
                return self.send(200, store.snapshot())
            if path.startswith("/audio/") and path.endswith(".mp3"):
                try:
                    audio = store.audio_path(path.removeprefix("/audio/").removesuffix(".mp3"))
                    return self.send(200, audio.read_bytes(), "audio/mpeg")
                except (ValueError, FileNotFoundError):
                    pass
            return self.send(404, {"error": "Not found."})

        def do_POST(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if (
                not self.valid_host()
                or self.headers.get("Origin") != origin
                or self.headers.get("X-Audition-Token") != token
            ):
                return self.send(403, {"error": "Reload the local audition page to continue."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 10000:
                    raise ValueError("Invalid request size.")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Expected a JSON object.")
                if self.path == "/api/sample":
                    result = store.synthesize(data.get("voice"))
                elif self.path == "/api/batch/start":
                    result = store.start_batch()
                elif self.path == "/api/batch/stop":
                    result = store.stop_batch()
                elif self.path == "/api/result":
                    result = store.save_result(data)
                elif self.path == "/api/refresh":
                    store.load_catalog(refresh=True)
                    result = store.snapshot()
                else:
                    return self.send(404, {"error": "Not found."})
                return self.send(200, result)
            except (ValueError, RuntimeError) as exc:
                return self.send(400, {"error": str(exc)})
            except Exception:
                return self.send(
                    502, {"error": "Request failed. Check the connection and try again; your saved ratings are safe."}
                )

    return Handler


class Command(BaseCommand):
    help = "Open a local Gemini voice comparison board; ratings and MP3s persist in .voice-auditions."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=8766)
        parser.add_argument(
            "--pre-generate", action="store_true", help="Cache every American English sample, then exit."
        )
        parser.add_argument("--workers", type=int, default=3, help="Concurrent requests for pre-generation (1–4).")
        parser.add_argument("--data-dir", default=str(Path(settings.BASE_DIR).parent / ".voice-auditions"))

    def handle(self, *args, **options):
        store = AuditionStore(options["data_dir"])
        if options["pre_generate"]:
            workers = max(1, min(options["workers"], 4))

            # Separate stores permit bounded concurrency; atomic MP3 publication
            # keeps the running browser server able to read completed samples.
            def generate(voice):
                worker = AuditionStore(options["data_dir"])
                worker.synthesize(voice)
                return voice

            pending = [
                v
                for v in store.voices
                if not (path := store.audio_path(store.sample_key(v))).exists() or not path.stat().st_size
            ]
            self.stdout.write(f"Generating {len(pending)} uncached samples with {workers} workers.")
            failures = []
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(generate, voice): voice for voice in pending}
                for count, future in enumerate(as_completed(futures), 1):
                    voice = futures[future]
                    try:
                        future.result()
                        self.stdout.write(f"[{count}/{len(pending)}] Saved {voice}")
                    except Exception as exc:
                        failures.append(voice)
                        self.stderr.write(f"[{count}/{len(pending)}] Failed {voice}: {exc}")
            self.stdout.write(f"Complete: {len(pending) - len(failures)} generated; {len(failures)} failed.")
            if failures:
                from django.core.management.base import CommandError

                raise CommandError("Failed voices (rerun to retry): " + ", ".join(failures))
            return
        server = ThreadingHTTPServer(("127.0.0.1", options["port"]), make_handler(store, secrets.token_urlsafe(32)))
        self.stdout.write(f"Voice auditions: http://127.0.0.1:{server.server_port}")
        self.stdout.write(
            f"{len(store.voices)} American English voices / {store.total} catalog voices. Ctrl-C to stop."
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
