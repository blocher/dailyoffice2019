"""Separate initial Gemini batch bootstrap (not scheduled and never on demand)."""

from datetime import date
from pathlib import Path

import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from office import audio_batch


class Command(BaseCommand):
    help = "Prepare, submit, inspect, and import a separate seven-day Gemini audio batch."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=("prepare", "submit", "status", "import", "attach"))
        parser.add_argument("--manifest", required=True, help="Local JSON manifest; keep it until import is complete.")
        parser.add_argument("--start-date", type=date.fromisoformat, help="First day (YYYY-MM-DD); defaults to today.")
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--batch-size", type=int, default=50)
        parser.add_argument("--chunk", type=int, help="Zero-based chunk to recover after an uncertain submission.")
        parser.add_argument("--job", help="Google batches/<id> for the attach action.")

    def handle(self, *args, **options):
        path = Path(options["manifest"]).expanduser().resolve()
        try:
            with audio_batch.manifest_lock(path):
                action = options["action"]
                if action == "prepare":
                    if path.exists():
                        raise ValueError("Manifest already exists; use a new path or resume the existing batch.")
                    manifest = audio_batch.prepare(
                        options["start_date"] or timezone.localdate(),
                        options["days"],
                        options["batch_size"],
                        self.stdout.write,
                    )
                    audio_batch.save_manifest(path, manifest)
                else:
                    manifest = audio_batch.load_manifest(path)
                    client = audio_batch.BatchClient()
                    if action == "submit":
                        audio_batch.submit(path, manifest, client)
                    elif action == "attach":
                        audio_batch.attach(path, manifest, client, options["chunk"], options["job"] or "")
                    else:
                        failures = audio_batch.refresh(path, manifest, client, action == "import", self.stdout.write)
                        if failures:
                            raise CommandError(f"{failures} failed jobs/clips; see failures in {path}.")
                imported = sum(bool(chunk.get("imported")) for chunk in manifest["chunks"])
                self.stdout.write(
                    f"{path}: {len(manifest['clips'])} clips, {len(manifest['chunks'])} batches, {imported} imported."
                )
        except requests.RequestException as exc:
            raise CommandError("Gemini network request failed; resume with the saved manifest.") from exc
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
