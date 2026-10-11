import os

from django.conf import settings
from django.core.management.base import BaseCommand

from office.api.views.tts import get_tts_provider

# Curated calm/reverent narration candidates from the Fish Audio library, keyed
# by reference_id. Use `--list` to see them and generate a sample for each so
# you can pick per-role voices, then set FISH_TTS_VOICE_* in the environment.
FISH_CANDIDATES = [
    ("536d3a5e000945adb7038665781a4aca", "Ethan", "male, calm, clear, authoritative (officiant)"),
    ("9032b5f2e2554b5a957ad655c052af16", "Slax (old)", "male, deep, calm, measured, storytelling"),
    ("1936333080804be19655c6749b2ae7b2", "Voice DL", "male, deep, calm, measured, serious"),
    ("bf322df2096a46f18c579d0baa36f41d", "Adrian", "male, deep, slow, measured (solemn)"),
    ("c5f56a6cc2ec4fa8920cb4c5889a3fb7", "Slax", "male, clear, crisp, smooth, neutral (reader)"),
    ("e3cd384158934cc9a01029cd7d278634", "Laura", "female, warm, calm, clear (congregation)"),
    ("b347db033a6549378b48d00acb0d06cd", "Selene", "female, soft, calm, gentle"),
    ("933563129e564b19a115bedd57b7406a", "Sarah", "female, soft, gentle, sincere"),
]

DEFAULT_TEXT = (
    "O Lord, open thou our lips. And our mouth shall show forth thy praise. "
    "Glory be to the Father, and to the Son, and to the Holy Spirit."
)


class Command(BaseCommand):
    help = (
        "Generate sample TTS clips so you can audition and pick voices. "
        "For Fish Audio, previews a curated set of reverent narration voices "
        "(or any reference_ids you pass) plus the currently configured roles."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--provider",
            default="fish",
            help="TTS provider to audition (default: fish). Falls back to TTS_PROVIDER for 'default'.",
        )
        parser.add_argument("--text", default=DEFAULT_TEXT, help="Text to synthesize for each sample.")
        parser.add_argument(
            "--voices",
            default="",
            help="Comma-separated voice ids (Fish reference_ids / OpenAI voice names) to audition "
            "instead of the curated list.",
        )
        parser.add_argument(
            "--out",
            default="",
            help="Output directory (default: MEDIA_ROOT/voice_auditions).",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Just print the curated candidates without generating audio.",
        )

    def handle(self, *args, **options):
        provider_name = None if options["provider"] == "default" else options["provider"]
        provider = get_tts_provider(provider_name)

        if options["list"]:
            self._print_candidates(provider)
            return

        voices = self._resolve_voices(provider, options["voices"])
        out_dir = options["out"] or os.path.join(settings.MEDIA_ROOT, "voice_auditions")
        os.makedirs(out_dir, exist_ok=True)

        self.stdout.write(
            self.style.WARNING(
                f"Auditioning {len(voices)} voice(s) with provider '{provider.name}' "
                f"(model={provider.model}, speed={provider.speed}) into {out_dir}"
            )
        )

        for voice, label in voices:
            safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:40]
            file_path = os.path.join(out_dir, f"{provider.name}_{safe_label}_{voice}.mp3")
            try:
                provider.synthesize(voice, options["text"], file_path)
                self.stdout.write(self.style.SUCCESS(f"  ok  {label} [{voice}] -> {file_path}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  fail {label} [{voice}]: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Listen to the clips in {out_dir} and set FISH_TTS_VOICE_*."))

    def _print_candidates(self, provider):
        self.stdout.write("Curated Fish Audio narration candidates:")
        for voice, label, notes in FISH_CANDIDATES:
            self.stdout.write(f"  {voice}  {label:14s} {notes}")
        self.stdout.write("\nCurrently configured roles:")
        for role in ("leader", "congregation", "reader"):
            self.stdout.write(f"  {role:13s} {provider.voices.get(role)}")

    def _resolve_voices(self, provider, voices_arg):
        if voices_arg:
            return [(v.strip(), v.strip()) for v in voices_arg.split(",") if v.strip()]
        if provider.name == "fish":
            candidates = [(voice, label) for voice, label, _ in FISH_CANDIDATES]
        else:
            # For non-Fish providers there is no curated library; audition the
            # three configured roles instead.
            candidates = []
        # Always include the configured per-role voices so you can compare.
        for role in ("leader", "congregation", "reader"):
            voice = provider.voices.get(role)
            if voice and voice not in {v for v, _ in candidates}:
                candidates.append((voice, f"configured-{role}"))
        return candidates
