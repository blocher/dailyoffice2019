import json
import re
import os
from django.core.management.base import BaseCommand
from office.models import Collect
from django.db.models import Q


class Command(BaseCommand):
    help = "Import Spanish collects from JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the JSON file containing Spanish collects")

    def handle(self, *args, **options):
        json_file_path = options["json_file"]

        # If path doesn't exist, check relative to importer directory
        if not os.path.exists(json_file_path):
            importer_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "collect_importer"
            )
            check_path = os.path.join(importer_dir, json_file_path)
            if os.path.exists(check_path):
                json_file_path = check_path
            else:
                self.stdout.write(self.style.ERROR(f"File not found: {json_file_path}"))
                return

        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.stdout.write(f"Loaded {len(data)} collects from {json_file_path}")

        updated_count = 0
        not_found_count = 0

        # Translation map for keywords
        TRANSLATIONS = {
            "PRIMER": "First",
            "PRIMERO": "First",
            "SEGUNDO": "Second",
            "TERCER": "Third",
            "TERCERO": "Third",
            "CUARTO": "Fourth",
            "QUINTO": "Fifth",
            "SEXTO": "Sixth",
            "SÉPTIMO": "Seventh",
            "OCTAVO": "Eighth",
            "ÚLTIMO": "Last",
            "PENÚLTIMO": "Last",
            "DOMINGO": "Sunday",
            "LUNES": "Monday",
            "MARTES": "Tuesday",
            "MIÉRCOLES": "Wednesday",
            "JUEVES": "Thursday",
            "VIERNES": "Friday",
            "SÁBADO": "Saturday",
            "ADVIENTO": "Advent",
            "NAVIDAD": "Christmas",
            "EPIFANÍA": "Epiphany",
            "CUARESMA": "Lent",
            "SEMANA": "Week",
            "SANTA": "Holy",
            "PASCUA": "Easter",
            "PENTECOSTÉS": "Pentecost",
            "TRINIDAD": "Trinity",
            "DÍA": "Day",
            "NOCHEBUENA": "Christmas Eve",
            "CIRCUNCISIÓN": "Circumcision",
            "SANTO": "Holy",
            "NOMBRE": "Name",
            "TODOS": "All",
            "SANTOS": "Saints",
            "CENIZA": "Ash",
            "RAMOS": "Palm",
            "ASCENSIÓN": "Ascension",
            "DE": "of",
            "EN": "in",
            "EL": "The",
            "LA": "The",
            "LOS": "The",
            "LAS": "The",
            "JESUCRISTO": "Jesus Christ",
            "SEÑOR": "Lord",
            "BAUTISMO": "Baptism",
            "PRESENTACIÓN": "Presentation",
            "VISITACIÓN": "Visitation",
            "TRANSFIGURACIÓN": "Transfiguration",
            "CONVERSIÓN": "Conversion",
            "NATIVIDAD": "Nativity",
            "ENCARNACIÓN": "Incarnation",
            "ANUNCIACIÓN": "Annunciation",
            "CONCEPCIÓN": "Conception",
            "SAN": "Saint",
            "ANDRÉS": "Andrew",
            "TOMÁS": "Thomas",
            "ESTEBAN": "Stephen",
            "JUAN": "John",
            "EVANGELISTA": "Evangelist",
            "INOCENTES": "Innocents",
            "PEDRO": "Peter",
            "PABLO": "Paul",
            "MATÍAS": "Matthias",
            "JOSÉ": "Joseph",
            "MARCOS": "Mark",
            "FELIPE": "Philip",
            "SANTIAGO": "James",
            "BERNABÉ": "Barnabas",
            "BAUTISTA": "Baptist",
            "MARÍA": "Mary",
            "MAGDALENA": "Magdalene",
            "VIRGEN": "Virgin",
            "BARTOLOMÉ": "Bartholomew",
            "CRUZ": "Cross",
            "MATEO": "Matthew",
            "MIGUEL": "Michael",
            "ÁNGELES": "Angels",
            "LUCAS": "Luke",
            "SIMÓN": "Simon",
            "JUDAS": "Jude",
            "PROPIO": "Proper",
            "TÉMPORAS": "Ember",
            "ROGACIÓN": "Rogation",
            "CAÍDOS": "Memorial",
            "CONMEMORACIÓN": "Day",
            "CANADÁ": "Canada",
            "INDEPENDENCIA": "Independence",
            "MISIONERO": "Missionary",
            "VIGILIA": "Vigil",
            "JERUSALÉN": "Jerusalem",
        }

        # Explicit Title Mappings for difficult cases
        TITLE_MAP = {
            "JUEVES SANTO": "Maundy Thursday",
            "VIERNES SANTO": "Good Friday",
            "SÁBADO SANTO": "Holy Saturday",
            "VIGILIA PASCUAL": "Easter Eve",
            "DÍA DE LA ASCENSIÓN": "Ascension Day",
            "SANTO TOMÁS": "Saint Thomas",
            "SANTO SANTIAGO": "Saint James",
            "DÍA DE LA INDEPENDENCIA": "Independence Day",
            "DÍA DE LOS CAÍDOS Y DÍA DE CONMEMORACIÓN": "Memorial Day & Remembrance Day",
            "DÍAS DE TÉMPORAS": "Ember Day (I)",  # Default to I
            "SANTO SANTIAGO DE JERUSALÉN": "Saint James of Jerusalem",
            "SEXTO DOMINGO DE PASCUA": "The Sixth Sunday of Easter: Rogation",
            "DÍA DE ACCIÓN DE GRACIAS": "Thanksgiving Day",
            "UNA ORACIÓN DE ACCIÓN DE GRACIAS": "Thanksgiving Day",
            "DOMINGO DE LA TRINIDAD": "Trinity Sunday",
            "DOMINGO DE RAMOS": "Palm Sunday",
            "EL QUINTO DOMINGO DE CUARESMA": "The Fifth Sunday in Lent: Passion Sunday",
            "DOMINGO DESPUÉS DE LA ASCENSIÓN": "The Sunday after the Ascension",
            "EL PENÚLTIMO DOMINGO DE EPIFANÍA": "World Mission Sunday",
            "PARA UN MÁRTIR": "Of a Martyr",
            "PARA UN PASTOR": "Of a Pastor",
            "PARA UN MISIONERO O EVANGELISTA": "Of a Missionary or Evangelist",
            "PARA UN MAESTRO DE LA FE": "Of a Teacher of the Faith",
            "PARA UN MONÁSTICO O RELIGIOSO": "Of a Monastic or Religious",
            "PARA UN ECUMENISTA": "Of an Ecumenist",
            "PARA UN REFORMADOR DE LA IGLESIA": "Of a Reformer of the Church",
            "PARA UN RENOVADOR DE LA SOCIEDAD": "Of a Renewer of Society",
            "PARA CUALQUIER CONMEMORACIÓN": "Of Any Commemoration (I)",
            "DÍA DE PASCUA": "Easter Day (I)",  # Default to I
        }

        # Pre-fetch candidates to avoid query in loop
        # Fetch all candidates EXCEPT occasional (which are matched by number)
        # This covers 'year', 'common_of_saints' (if separate), etc.
        year_candidates = list(Collect.objects.exclude(collect_type__key="occasional"))

        for item in data:
            match = None

            # 1. Try matching by Number (Occasional)
            if item.get("number"):
                try:
                    match = Collect.objects.filter(collect_type__key="occasional", number=item["number"]).first()
                except Exception as e:
                    pass

            # 2. Try matching by Title (Year/Other)
            if not match and item.get("title"):
                title = item["title"].upper().strip()

                # Handle Special Rogation Case (I and II)
                if title == "DÍAS DE ROGACIÓN":
                    # Check body to disambiguate or use order
                    body_start = item.get("body", "").strip().lower()
                    subtitle = item.get("subtitle") or ""

                    if "agricultura" in subtitle.lower() or "cosechas" in body_start:
                        # Agriculture -> Rogation Day (I)
                        mapped_title = "Rogation Day (I)"
                    elif "industrias" in subtitle.lower() or "industrias" in body_start or "trabajo" in body_start:
                        # Industry -> Rogation Day (II)
                        mapped_title = "Rogation Day (II)"
                    else:
                        # Fallback heuristic
                        if "cosechas" in body_start:
                            mapped_title = "Rogation Day (I)"
                        else:
                            mapped_title = "Rogation Day (II)"

                    for c in year_candidates:
                        if c.title.lower() == mapped_title.lower():
                            match = c
                            break

                # Handle Special Easter Case (I and II)
                elif title == "DÍA DE PASCUA":
                    # Check if body contains specific phrases
                    body = item.get("body", "").lower()
                    if "abrió la puerta de la vida eterna" in body:
                        mapped_title = "Easter Day (I)"
                    else:
                        mapped_title = "Easter Day (II)"

                    for c in year_candidates:
                        if c.title.lower() == mapped_title.lower():
                            match = c
                            break

                # Handle Ember Days
                elif title == "DÍAS DE TÉMPORAS":
                    body = item.get("body", "").lower()
                    subtitle = item.get("subtitle") or ""
                    if "instituido varias órdenes" in body or "ministerio de la iglesia" in subtitle.lower():
                        mapped_title = "Ember Day (I)"
                    else:
                        mapped_title = "Ember Day (II)"

                    for c in year_candidates:
                        if c.title.lower() == mapped_title.lower():
                            match = c
                            break

                # Handle Any Commemoration (I and II)
                elif title == "PARA CUALQUIER CONMEMORACIÓN":
                    body = item.get("body", "").lower()
                    if "nube de testigos" in body:
                        mapped_title = "Of Any Commemoration (I)"
                    else:
                        mapped_title = "Of Any Commemoration (II)"

                    for c in year_candidates:
                        if c.title.lower() == mapped_title.lower():
                            match = c
                            break

                # Check TITLE_MAP first
                elif title in TITLE_MAP:
                    mapped_title = TITLE_MAP[title]
                    # Find candidate with this title
                    for c in year_candidates:
                        if c.title.lower() == mapped_title.lower():
                            match = c
                            break
                    if not match:
                        # Try fuzzy match against mapped title?
                        pass

                if not match:
                    translated_keywords = set()

                    # Special handling for PROPIO (Proper)
                    if "PROPIO" in title:
                        # Extract number
                        num_match = re.search(r"PROPIO\s+(\d+)", title)
                        if num_match:
                            proper_num = num_match.group(1)
                            # Match "Proper {num}"
                            translated_keywords.add("Proper")
                            translated_keywords.add(proper_num)
                    else:
                        words = re.findall(r"\w+", title)
                        for w in words:
                            if w in TRANSLATIONS:
                                tr = TRANSLATIONS[w]
                                for part in tr.split():
                                    translated_keywords.add(part)

                    # Search candidates
                    best_candidate = None
                    max_score = 0

                    for candidate in year_candidates:
                        cand_title = candidate.title
                        cand_words = set(re.findall(r"\w+", cand_title))

                        if not translated_keywords:
                            continue

                        intersection = len(translated_keywords.intersection(cand_words))
                        score = intersection / len(translated_keywords)

                        if score > max_score:
                            max_score = score
                            best_candidate = candidate

                    if best_candidate and max_score >= 0.6:
                        match = best_candidate

            if match:
                # Update fields
                match.spanish_title = item.get("title")
                match.spanish_subtitle = item.get("subtitle")
                match.spanish_attribution = item.get("attribution")

                body = item.get("body", "")
                if body and not body.startswith("<p>"):
                    match.spanish_text = f"<p>{body}</p>"
                else:
                    match.spanish_text = body

                match.normalized_spanish_text = re.sub(r"<[^>]+>", "", body).lower()

                match.save()
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"No match found for: {item.get('title')} (#{item.get('number')})")
                )
                not_found_count += 1

        self.stdout.write(self.style.SUCCESS(f"Finished. Updated: {updated_count}, Not Found: {not_found_count}"))
