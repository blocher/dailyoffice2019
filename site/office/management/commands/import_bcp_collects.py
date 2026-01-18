import pdfplumber
import re
import os
from django.core.management.base import BaseCommand
from office.models import Collect


class Command(BaseCommand):
    help = "Import remaining Spanish collects from the full BCP PDF"

    def add_arguments(self, parser):
        parser.add_argument("pdf_file", type=str, help="Path to the Spanish BCP PDF")

    def handle(self, *args, **options):
        pdf_path = options["pdf_file"]

        # Resolve path
        if not os.path.exists(pdf_path):
            importer_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "collect_importer"
            )
            check_path = os.path.join(importer_dir, pdf_path)
            if os.path.exists(check_path):
                pdf_path = check_path
            else:
                self.stdout.write(self.style.ERROR(f"File not found: {pdf_path}"))
                return

        self.stdout.write(f"Scanning {pdf_path}...")

        # 1. Fetch missing collects (excluding year/occasional which are mostly done)
        # We need "office_prayers", "burial_rite", etc.
        missing_collects = Collect.objects.filter(spanish_text__isnull=True).exclude(
            collect_type__uuid="b1c89797-8afd-4347-9583-3e79f3096680"
        )

        # Create a dictionary of English title -> Collect object for faster lookup
        missing_dict = {c.title.lower(): c for c in missing_collects}
        self.stdout.write(f"Found {len(missing_dict)} missing collects to search for.")

        # Keywords to search for in PDF to locate relevant sections
        # Office Prayers are in "OFICIO DIARIO" (Daily Office) ~ Page 11
        # Burial in "SEPULTURA DE LOS DIFUNTOS" ~ Page 249

        # We will iterate through pages and look for matches
        # This is a "fuzzy match" approach because we don't know the exact Spanish titles for many.
        # But for some we can guess.

        # Mapping English Title -> Spanish Search String (or regex)
        # This needs to be populated with common matches

        KNOWN_MAPPINGS = {
            "A Prayer for Mission": "Por la misión",  # "Oh Dios, hiciste de una sola sangre..."
            "A Collect for Grace": "Colecta por gracia",  # "Señor Dios, todopoderoso y eterno..."
            "A Collect for Peace": "Colecta por la paz",
            "A Collect for Guidance": "Colecta por guía",
            "For the Clergy and People": "Por el clero y el pueblo",
            "A Prayer of St. John Chrysostom": "Oración de San Juan Crisóstomo",
            "The Grace": "La gracia de nuestro Señor Jesucristo",
            "At the Burial of a Child": "Entierro de un niño",
            "Confession of Sin": "Confesión",  # Generic, need context
            "The General Thanksgiving": "Acción de gracias general",
            "Prayer for the Whole State of Christ's Church": "Oración por el estado de la Iglesia",
            "Te Deum Laudamus": "Te Deum",
            "Benedictus": "Benedictus",
            "Magnificat": "Magnificat",
            "Nunc Dimittis": "Nunc Dimittis",
            "Phos Hilaron": "Oh luz radiante",
            # Add more as we find them
        }

        # Let's extract text and look for these
        # Since the file is large, we might want to target specific pages if we knew them.
        # But scanning all is safer.

        matches_found = 0

        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            # Limit pages? The TOC says mostly 1-300 for rites. Psalms are 270+.
            # We can scan first 300 pages.
            for i, page in enumerate(pdf.pages[:300]):
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        # Now search in full_text
        # Strategy: Search for known headers or body snippets associated with the missing collects.
        # Since we don't have the Spanish text in DB, we rely on KNOWN_MAPPINGS or common translations.

        # Better approach:
        # 1. Iterate over missing collects
        # 2. Try to find their English title translated? No.
        # 3. Use a predefined map of "English Title" -> "Spanish Title" (as much as we can guess)
        # 4. Extract the body following that title in the text.

        # Let's try to find "A Collect for Peace" (Colecta por la paz)

        # Refined regex for collecting body: Title -> Body -> "Amen" or next Title.

        for eng_title, collect in missing_dict.items():
            search_term = KNOWN_MAPPINGS.get(collect.title, None)
            if not search_term:
                # Try simple heuristic?
                # "Collect for Peace" -> "Colecta por la paz"
                if "peace" in eng_title:
                    search_term = "paz"
                elif "grace" in eng_title:
                    search_term = "gracia"
                elif "guidance" in eng_title:
                    search_term = "guía"
                # This is weak.

            if search_term:
                # Find search_term in text
                # ... this is complex to implement robustly without exact strings.
                pass

        # Since I cannot easily interactively browse the PDF content via code in one go,
        # I will start by dumping specific sections to console to identify titles manually
        # OR assume standard translations for major Office collects.

        # Let's target the Daily Office first (Pages 11-70 approx)
        self.extract_office_collects(pdf_path, missing_dict)
        # Target Burial Rite (Pages 249-268)
        self.extract_burial_collects(pdf_path, missing_dict)

    def extract_burial_collects(self, pdf_path, missing_dict):
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[248:268]:  # 249-268 roughly
                t = page.extract_text()
                if t:
                    text += t + "\n"

        # Burial Collects phrases
        burial_phrases = {
            "For Those Who Mourn": "Dios Todopoderoso, Padre de toda misericordia y dador de todo consuelo",
            "At a Burial": "Oh Dios, cuya misericordia es infinita",  # Often "O God whose mercies cannot be numbered"
            "The Commendation": "En tus manos, oh Padre misericordioso",
            "For the Dead": "Acuérdate de tu siervo",
            "A Commendatory Prayer": "En tus manos, oh Padre misericordioso",
            "A Collect for Faith": "Señor Jesucristo, por tu muerte",  # Guessing
        }

        updated = 0
        for eng_key, phrase in burial_phrases.items():
            target = missing_dict.get(eng_key.lower())
            if not target:
                # Fuzzy match
                for k, v in missing_dict.items():
                    if eng_key.lower() in k:
                        target = v
                        break

            if target:
                escaped_phrase = re.escape(phrase).replace(r"\ ", r"\s+")
                pattern = escaped_phrase + r"(.*?)\s+Amén"
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    body = phrase + match.group(1).strip()  # Include start phrase
                    body = re.sub(r"\s+", " ", body)
                    target.spanish_text = f"<p>{body} Amén.</p>"
                    target.save()
                    updated += 1
                    self.stdout.write(f"Updated Burial '{target.title}'")

        self.stdout.write(f"Burial Collects Updated: {updated}")

    def extract_office_collects(self, pdf_path, missing_dict):
        # Extract pages 11-70 (Morning/Evening/Compline/Midday)
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[10:80]:
                t = page.extract_text()
                if t:
                    text += t + "\n"

        # Look for standard headers or PHRASES
        # Title matching is unreliable due to translation variations.
        # Phrase matching (first 5-10 words) is better if we can guess the Spanish.

        # Office Prayers mappings (English Title -> Likely Spanish Phrase Start)
        office_phrases = {
            "A Collect for Peace": "Oh Dios, autor de la paz y amante de la concordia",  # Morning
            "A Collect for Grace": "Señor, nuestro Padre celestial, Dios todopoderoso y eterno",  # Morning
            "A Collect for Guidance": "Padre Celestial, en ti vivimos y nos movemos",  # Morning
            "A Prayer for Mission": "Oh Dios, hiciste de una sola sangre a todos los pueblos",  # Morning/Evening
            "A Collect for the Presence of Christ": "Señor Jesús, quédate con nosotros",  # Evening
            "A Collect for Aid against Perils": "Ilumina nuestras tinieblas",  # Evening
            "A Collect for Resurrection Hope": "Señor Dios, cuya Hijo nuestro Salvador Jesucristo triunfó sobre la muerte",  # Compline (Check phrasing)
            "A Prayer of St. John Chrysostom": "Dios Todopoderoso, que nos has dado la gracia",
            "The Grace": "La gracia de nuestro Señor Jesucristo",
            "For the Clergy and People": "Dios Todopoderoso y eterno, de quien procede todo don",
        }

        updated = 0
        for eng_key, phrase in office_phrases.items():
            # Find matching collect in missing_dict
            target = missing_dict.get(eng_key.lower())
            if not target:
                # Fuzzy match
                for k, v in missing_dict.items():
                    if eng_key.lower() in k:
                        target = v
                        break

            if target:
                # Regex: Phrase ... Amén
                # Allow for some variation in spaces/punctuation
                escaped_phrase = re.escape(phrase).replace(r"\ ", r"\s+")
                pattern = escaped_phrase + r"(.*?)\s+Amén"

                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    body = phrase + match.group(1).strip()
                    body = re.sub(r"\s+", " ", body)
                    target.spanish_text = f"<p>{body} Amén.</p>"
                    target.save()
                    updated += 1
                    self.stdout.write(f"Updated Office '{target.title}'")

        self.stdout.write(f"Office Collects Updated: {updated}")
