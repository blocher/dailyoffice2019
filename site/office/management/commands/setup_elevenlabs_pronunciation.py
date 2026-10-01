from django.conf import settings
from django.core.management.base import BaseCommand
import requests


# One token, not "ah men". A lone "ah" is the drawn-out interjection.
# Acute on e (ahmén) puts stress on the second syllable, Latin ah-MEN.
AMEN_ALIAS = "ahmén"


class Command(BaseCommand):
    help = (
        "Create or update an ElevenLabs pronunciation dictionary that keeps "
        "printed 'Amen' but speaks the liturgical Latin form. Prints IDs for .env."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--alias",
            default=AMEN_ALIAS,
            help=f"Spoken alias for Amen (default: {AMEN_ALIAS}).",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Replace the Amen rule on the dictionary already in settings.",
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, "ELEVENLABS_API_KEY", "")
        if not api_key:
            self.stderr.write(self.style.ERROR("ELEVENLABS_API_KEY is not configured."))
            return

        alias = options["alias"]
        dictionary_id = getattr(settings, "ELEVENLABS_PRONUNCIATION_DICTIONARY_ID", "")
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        rule = {
            "type": "alias",
            "string_to_replace": "Amen",
            "alias": alias,
            "case_sensitive": False,
            "word_boundaries": True,
        }

        if options["update"] or dictionary_id:
            if not dictionary_id:
                self.stderr.write(self.style.ERROR("ELEVENLABS_PRONUNCIATION_DICTIONARY_ID is not configured."))
                return
            response = requests.post(
                f"https://api.elevenlabs.io/v1/pronunciation-dictionaries/{dictionary_id}/add-rules",
                headers=headers,
                json={"rules": [rule]},
                timeout=60,
            )
            action = "Updated"
        else:
            response = requests.post(
                "https://api.elevenlabs.io/v1/pronunciation-dictionaries/add-from-rules",
                headers=headers,
                json={
                    "name": "Daily Office liturgy",
                    "description": "Liturgical pronunciations for office audio. v2 uses alias rules, not IPA.",
                    "rules": [rule],
                },
                timeout=60,
            )
            action = "Created"

        try:
            response.raise_for_status()
        except requests.HTTPError:
            self.stderr.write(self.style.ERROR(f"ElevenLabs error {response.status_code}: {response.text}"))
            return

        data = response.json()
        dictionary_id = data.get("id") or dictionary_id
        version_id = data.get("version_id")
        self.stdout.write(self.style.SUCCESS(f"{action} ElevenLabs pronunciation dictionary."))
        self.stdout.write(f"Amen alias is now {alias!r}.")
        self.stdout.write("Put these in site/website/.env and restart Django:")
        self.stdout.write(f"ELEVENLABS_PRONUNCIATION_DICTIONARY_ID={dictionary_id}")
        self.stdout.write(f"ELEVENLABS_PRONUNCIATION_DICTIONARY_VERSION_ID={version_id}")
        self.stdout.write("Then regenerate Amen clips from admin.")
