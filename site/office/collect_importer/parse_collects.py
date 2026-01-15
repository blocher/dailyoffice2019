import pdfplumber
import json
import re
import os


def parse_spanish_collects(pdf_path):
    # Resolve relative path if needed, assuming run from project root
    if not os.path.exists(pdf_path):
        # Try relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, os.path.basename(pdf_path))

    print(f"Parsing {pdf_path}...")
    collects = []

    ignored_headers = {
        "COLECTAS Y",
        "ORACIONES OCASIONALES",
        "COLECTAS DEL",
        "COLECTAS",
        "AÑO CRISTIANO",
        "ADVIENTO",
        "NAVIDAD",
        "EPIFANÍA",
        "CUARESMA",
        "SEMANA SANTA",
        "PASCUA",
        "EL TIEMPO DE PENTECOSTÉS",
        "PREFACIO",
        "TEMPORADA",
        "SEMANAS",
        "DÍAS",
        "SANTOS",
        "COMÚN DE CONMEMORACIONES",
    }

    # Common starts of prayers to distinguish body from subtitle
    prayer_starts = ("Dios", "Oh Dios", "Padre", "Señor", "Concédenos", "Danos", "Bendito", "Mueve", "Te", "Cristo")

    text_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                lines = extracted.split("\n")
                # Filter page numbers (digits only)
                lines = [l for l in lines if not re.match(r"^\d+$", l.strip())]
                text_lines.extend(lines)

    current_collect = {}  # title, subtitle, date, body_lines
    last_saved_title = None

    def save_collect():
        nonlocal last_saved_title
        if current_collect.get("title") and current_collect.get("body_lines"):
            last_saved_title = current_collect["title"]
            body = " ".join(current_collect["body_lines"]).strip()
            # Basic cleanup
            body = body.replace("- ", "")  # Hyphenation

            collects.append(
                {
                    "title": current_collect["title"],
                    "subtitle": current_collect.get("subtitle"),
                    "date": current_collect.get("date"),
                    "body": body,
                    "file": "spanish_collects.pdf",
                }
            )
        current_collect.clear()

    iterator = iter(text_lines)

    for line in text_lines:
        line = line.strip()
        if not line:
            continue

        # 1. Check for Prefacio (end of collect)
        if line.lower().startswith("prefacio"):
            save_collect()
            continue

        # Check for Alternative Collect (o este)
        if line.startswith("o este") or line.startswith("o esto"):
            # Alternative collect. Use last saved title.
            save_collect()
            if last_saved_title:
                current_collect["title"] = last_saved_title
            continue

        # 2. Check for Date (Enero 1)
        if re.match(
            r"^(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)\s+\d+$", line
        ):
            current_collect["date"] = line
            continue

        # 3. Check for Rubrics
        if (
            line.startswith("La Colecta ")
            or line.startswith("Cuando ")
            or line.startswith("Miércoles, viernes")
            or line.startswith("Esta Colecta")
            or line.startswith("Las colectas para")
        ):
            # Rubrics separate collects
            save_collect()
            continue

        # 4. Check for Title (UPPERCASE)
        # Some titles are long.
        if line.isupper() and len(line) > 3:
            # Check ignored
            is_ignored = False
            for h in ignored_headers:
                if h in line:  # partial match for "COLECTAS del AÑO..."
                    # Exact match or starts with?
                    if line == h:
                        is_ignored = True
                    elif line.startswith(h) and len(line) < len(h) + 5:
                        is_ignored = True

            # Additional check: specific headers
            if "COLECTAS del" in line:
                is_ignored = True

            if not is_ignored:
                save_collect()
                current_collect["title"] = line
                continue
            else:
                # Header acts as separator
                save_collect()
                continue

        # 5. Body or Subtitle
        if current_collect.get("title"):
            # If body hasn't started, check if this line is a subtitle
            if "body_lines" not in current_collect:
                # Heuristic: If line doesn't start with common prayer start, might be subtitle.
                # BUT some prayers start uniquely.
                # Subtitles are usually short and Mixed Case.
                first_word = line.split()[0].strip(",:")

                is_prayer_start = first_word in prayer_starts

                # If it's a date line that was missed? No, regex caught dates.

                # "Anunciación" -> Subtitle
                # "El bautismo de Nuestro Señor" -> Subtitle
                # "La Manifestación de Cristo a los gentiles" -> Subtitle

                # Check for "Amen." in line?

                if (
                    not is_prayer_start
                    and len(line) < 60
                    and not line.endswith("Amén.")
                    and not line.endswith("Amen.")
                ):
                    # Assume subtitle
                    # But be careful. "Dios Todopoderoso, danos la gracia..."
                    # "Dios" is in prayer_starts.

                    # What if subtitle starts with "Dios"? Unlikely.

                    current_collect["subtitle"] = line
                    # Init body lines
                    current_collect["body_lines"] = []
                else:
                    # Start body
                    current_collect.setdefault("body_lines", []).append(line)
            else:
                # Body continuation
                current_collect["body_lines"].append(line)

    save_collect()
    return collects


def parse_spanish_occasional(pdf_path):
    if not os.path.exists(pdf_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, os.path.basename(pdf_path))

    print(f"Parsing {pdf_path}...")
    collects = []

    text_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        # Skip TOC, start page 6 (index 5)
        for page in pdf.pages[5:]:
            extracted = page.extract_text()
            if extracted:
                lines = extracted.split("\n")
                # Filter page numbers
                lines = [l for l in lines if not re.match(r"^\d+$", l.strip())]
                text_lines.extend(lines)

    current_data = {}  # number, title, attribution, body_lines

    def save_current():
        if current_data.get("number") and current_data.get("body_lines"):
            body = " ".join(current_data["body_lines"]).strip()
            body = body.replace("- ", "")
            collects.append(
                {
                    "number": current_data["number"],
                    "title": current_data["title"],
                    "attribution": current_data.get("attribution"),
                    "body": body,
                    "file": "spanish_ocassiona.pdf",
                }
            )
        current_data.clear()

    for line in text_lines:
        line = line.strip()
        if not line:
            continue

        # New prayer: "1. TITLE"
        # Special case: "3O. TITLE" (The PDF has a typo 30 -> 3O)
        match = re.match(r"^(\d+|3O)\.\s+(.*)$", line)
        if match:
            save_current()

            num_str = match.group(1)
            if num_str == "3O":
                num = 30
            else:
                num = int(num_str)

            rest = match.group(2)

            # Split title/attribution
            words = rest.split()
            title_words = []
            attr_words = []
            found_lower = False

            for w in words:
                clean_w = w.strip(".,;")
                if not clean_w:
                    continue

                has_lower = any(c.islower() for c in clean_w)
                # Check if it is a connector like "de", "la", "el", "los", "las", "y", "del", "al" in title
                # BUT titles in this PDF seem ALL CAPS.
                # "POR LA IGLESIA UNIVERSAL"

                if has_lower:
                    found_lower = True

                if found_lower:
                    attr_words.append(w)
                else:
                    title_words.append(w)

            title = " ".join(title_words)
            attribution = " ".join(attr_words) if attr_words else None

            current_data = {"number": num, "title": title, "attribution": attribution, "body_lines": []}
        else:
            # Body or ignored header
            # Ignore headers like "LA IGLESIA" (Upper case, no number)
            # Only if we are not in a body?
            # Or if line is short and Upper Case?
            if line.isupper() and len(line) < 50:
                # Likely header.
                # But check if it is part of body?
                # Body usually Mixed Case.
                pass
            elif line.lower() == "amén." or line.lower() == "amen.":
                if current_data:
                    current_data["body_lines"].append(line)
                    save_current()
            else:
                if current_data:
                    current_data["body_lines"].append(line)

    save_current()
    return collects


if __name__ == "__main__":
    # Default to files in the same directory if running as script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    c1 = parse_spanish_collects(os.path.join(script_dir, "spanish_collects.pdf"))
    c2 = parse_spanish_occasional(os.path.join(script_dir, "spanish_ocassiona.pdf"))

    all_collects = c1 + c2
    print(f"Extracted {len(c1)} collects from collects PDF")
    print(f"Extracted {len(c2)} collects from occasional PDF")

    output_path = os.path.join(script_dir, "spanish_collects.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_collects, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
