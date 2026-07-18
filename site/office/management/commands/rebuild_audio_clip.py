import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

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

    def _prune_orphans(self, is_dry_run):
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            self.stdout.write(self.style.ERROR(f"Media root does not exist: {media_root}"))
            return
        known = set(AudioClip.objects.values_list("filename", flat=True))
        orphans = []
        for filename in os.listdir(media_root):
            if not filename.endswith(".mp3"):
                continue
            if filename in known:
                continue
            orphans.append(filename)

        deleted = 0
        freed_bytes = 0
        for filename in orphans:
            file_path = os.path.join(media_root, filename)
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
