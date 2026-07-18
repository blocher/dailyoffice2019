import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from office.api.views.tts import provider_names
from office.models import AudioClip


class Command(BaseCommand):
    help = (
        "Manage individual TTS audio clips tracked in the AudioClip table: "
        "rebuild specific clips, backfill rows for existing files, drop clips "
        "for a retired voice, or prune orphaned mp3 files with no DB row."
    )

    def add_arguments(self, parser):
        parser.add_argument("--key", help="Delete the clip with this key so it regenerates on next request.")
        parser.add_argument(
            "--text",
            help="Delete clips whose stored (normalized) text contains this string (case-insensitive).",
        )
        parser.add_argument("--drop-voice", help="Delete all clips generated with this voice (e.g. alloy, ash).")
        parser.add_argument(
            "--clear-provider",
            help="Delete ALL generated audio (files + AudioClip rows) for a provider's subfolder, "
            "e.g. 'fish' or 'openai'. Use 'legacy' for files stored at the media root before "
            "per-provider subfolders existed. Pass 'all' to clear every provider plus legacy.",
        )
        parser.add_argument(
            "--prune-orphans",
            action="store_true",
            help="Delete on-disk mp3 files in MEDIA_ROOT that have no matching AudioClip row.",
        )
        parser.add_argument(
            "--backfill",
            action="store_true",
            help="Walk the standard office/settings matrix to populate AudioClip rows "
            "for existing (and generate missing) clips. Runs update_audio_files.",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually delete/rebuild. Without this, destructive actions run as a dry run.",
        )

    def handle(self, *args, **options):
        is_dry_run = not options["execute"]
        did_something = False

        if options["backfill"]:
            did_something = True
            self.stdout.write(self.style.WARNING("Backfilling AudioClip rows via update_audio_files..."))
            # Generation/recording happens as a side effect of serving each office.
            call_command("update_audio_files")
            self.stdout.write(self.style.SUCCESS("Backfill complete."))

        if options["key"]:
            did_something = True
            self._delete_queryset(AudioClip.objects.filter(key=options["key"]), is_dry_run, "key")

        if options["text"]:
            did_something = True
            self._delete_queryset(AudioClip.objects.filter(text__icontains=options["text"]), is_dry_run, "text")

        if options["drop_voice"]:
            did_something = True
            self._delete_queryset(
                AudioClip.objects.filter(voice=options["drop_voice"]), is_dry_run, f"voice={options['drop_voice']}"
            )

        if options["clear_provider"]:
            did_something = True
            target = options["clear_provider"].lower()
            targets = provider_names() + ["legacy"] if target == "all" else [target]
            for name in targets:
                self._clear_provider(name, is_dry_run)

        if options["prune_orphans"]:
            did_something = True
            self._prune_orphans(is_dry_run)

        if not did_something:
            self.stdout.write(
                self.style.WARNING(
                    "Nothing to do. Pass one of --key, --text, --drop-voice, --prune-orphans, or --backfill."
                )
            )
            return

        if is_dry_run and not options["backfill"]:
            self.stdout.write(self.style.WARNING("This was a dry run. Re-run with --execute to apply."))

    def _delete_queryset(self, queryset, is_dry_run, label):
        clips = list(queryset)
        if not clips:
            self.stdout.write(self.style.WARNING(f"No clips matched {label}."))
            return
        deleted_files = 0
        for clip in clips:
            if is_dry_run:
                self.stdout.write(f"Would delete [{label}] {clip.filename}: {clip.text[:60]!r}")
                continue
            if clip.delete_file():
                deleted_files += 1
            clip.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted [{label}] {clip.filename}"))
        if not is_dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Removed {len(clips)} clip record(s) and {deleted_files} file(s) for {label}.")
            )

    def _clear_provider(self, name, is_dry_run):
        """Delete every generated file (and matching AudioClip rows) for a
        provider subfolder. ``legacy`` targets pre-subfolder files stored
        directly in the media root."""
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            self.stdout.write(self.style.ERROR(f"Media root does not exist: {media_root}"))
            return

        if name == "legacy":
            # Loose office audio directly under the media root (no subfolder):
            # per-clip/combined mp3s and leftover ffmpeg concat lists.
            target_dir = media_root
            files = [
                f
                for f in os.listdir(media_root)
                if os.path.isfile(os.path.join(media_root, f)) and (f.endswith(".mp3") or f.endswith(".mp3.txt"))
            ]
            rows = AudioClip.objects.exclude(filename__contains="/")
        else:
            target_dir = os.path.join(media_root, name)
            files = []
            if os.path.isdir(target_dir):
                for entry in os.listdir(target_dir):
                    full = os.path.join(target_dir, entry)
                    if os.path.isfile(full) and (entry.endswith(".mp3") or entry.endswith(".mp3.txt")):
                        files.append(entry)
            rows = AudioClip.objects.filter(filename__startswith=f"{name}/")

        row_count = rows.count()
        if not files and not row_count:
            self.stdout.write(self.style.WARNING(f"Nothing to clear for provider '{name}'."))
            return

        freed_bytes = 0
        for entry in files:
            file_path = os.path.join(target_dir, entry)
            size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            if is_dry_run:
                self.stdout.write(f"Would clear [{name}] {entry} ({size / 1024 / 1024:.2f} MB)")
                continue
            try:
                os.remove(file_path)
                freed_bytes += size
            except OSError as e:
                self.stdout.write(self.style.ERROR(f"Could not remove {entry}: {e}"))

        if is_dry_run:
            self.stdout.write(
                self.style.WARNING(f"[{name}] Would delete {len(files)} file(s) and {row_count} AudioClip row(s).")
            )
            return

        rows.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"[{name}] Deleted {len(files)} file(s) ({freed_bytes / 1024 / 1024:.2f} MB) "
                f"and {row_count} AudioClip row(s)."
            )
        )

    def _prune_orphans(self, is_dry_run):
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            self.stdout.write(self.style.ERROR(f"Media root does not exist: {media_root}"))
            return
        known = set(AudioClip.objects.values_list("filename", flat=True))
        # Scan the media root top level plus each provider subfolder. Other
        # pipelines' directories (e.g. audio_gemini) are deliberately skipped.
        scan_dirs = [("", media_root)]
        for name in provider_names():
            provider_dir = os.path.join(media_root, name)
            if os.path.isdir(provider_dir):
                scan_dirs.append((name, provider_dir))

        orphans = []  # (rel_name_for_known_lookup, absolute_path)
        for prefix, directory in scan_dirs:
            for entry in os.listdir(directory):
                if not entry.endswith(".mp3"):
                    continue
                full = os.path.join(directory, entry)
                if not os.path.isfile(full):
                    continue
                rel_name = f"{prefix}/{entry}" if prefix else entry
                if rel_name in known:
                    continue
                orphans.append((rel_name, full))

        deleted = 0
        freed_bytes = 0
        for filename, file_path in orphans:
            size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            if is_dry_run:
                self.stdout.write(f"Would prune orphan: {filename} ({size / 1024 / 1024:.2f} MB)")
                continue
            try:
                os.remove(file_path)
                deleted += 1
                freed_bytes += size
                self.stdout.write(self.style.SUCCESS(f"Pruned orphan: {filename}"))
            except OSError as e:
                self.stdout.write(self.style.ERROR(f"Could not remove {filename}: {e}"))

        self.stdout.write("\n" + "=" * 40)
        self.stdout.write(self.style.SUCCESS(f"Orphan mp3 files found: {len(orphans)}"))
        if not is_dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Pruned {deleted} file(s), freed {freed_bytes / 1024 / 1024:.2f} MB")
            )
