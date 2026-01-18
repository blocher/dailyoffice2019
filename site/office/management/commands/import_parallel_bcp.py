import pdfplumber
import re
import os
from django.core.management.base import BaseCommand
from office.models import Collect


class Command(BaseCommand):
    help = "Import remaining Spanish collects from the full BCP PDF using parallel English PDF"

    def add_arguments(self, parser):
        parser.add_argument("eng_pdf", type=str, help="Path to the English BCP PDF")
        parser.add_argument("spa_pdf", type=str, help="Path to the Spanish BCP PDF")

    def handle(self, *args, **options):
        # Normalization helper
        def normalize(s):
            return s.replace("’", "'").replace("“", '"').replace("”", '"')

        eng_path = options["eng_pdf"]
        spa_path = options["spa_pdf"]

        # Resolve paths
        importer_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "collect_importer"
        )
        if not os.path.exists(eng_path):
            eng_path = os.path.join(importer_dir, eng_path)
        if not os.path.exists(spa_path):
            spa_path = os.path.join(importer_dir, spa_path)

        # Missing Collects
        # Update filter to include ALL collects, not just missing ones?
        # The user list implies specific ones are missing.
        # But my filter might be excluding some that have partial data?
        # missing_collects = Collect.objects.filter(spanish_text__isnull=True)...

        # Override missing_collects query to target SPECIFIC titles provided by user to ensure we look for them
        # even if DB thinks they have something (or if my filter was wrong).

        specific_targets = [
            "In the Time of any Common Plague or Sickness",
            "At a Burial of a Veteran of the Armed Forces.",
            "Prayer for the Great Plague of 1665",
            "Confession of Sin (Holy Eucharist: Standard Anglican)",
            "Solemn Collect for Ourselves",
            "For Those Who Mourn, at the Burial",
            "In Time of Great Sickness and Mortality",
            "For the Ordination of Deacons",
            "Prayer for a Vigil",
            "Blessing of the Font or Basin",
            "For Those Still in Our Pilgrimage",
            "At the Litany of Penitence",
            "Prayer for the Child",
            "The Ordination of Priests",
            "Concluding Collect for the Dead",
            "For the Blessing of a Grave",
            "Before the Commendation",
            "Solemn Collect against Hersey and Schism",
            "Consecration of a Place of Worship",
            "The Post Communion Prayer (Renewed Ancient)",
            "Solemn Collect for Our Bishops",
            "Confession of Sin (Holy Eucharist: Ancient Renewed)",
            "For the Institution of a Rector",
            "Opening Collect for the Consecration of a Place of Worship",
            "The Post Communion Prayer (Anglican Standard)",
            "Blessing and Consecration of the Holy Table",
            "Solemn Collect against Evil, Sickness, and Pestilence",
            "Solemn Collect for Unbelievers",
            "For Blessing on a Marriage",
            "Solemn Collect for Our Leaders",
            "Collect of a New Rector",
            "The Consecration of a Bishop",
            "Thanksgiving over Water",
            "Prayer for Baptismal Candidates",
            "For Those Who Mourn",
            "At the Palm Procession",
            "Compline Antiphon",
            "A Prayer for the Dead",
            "For the Gift of Children in Marriage",
            "At Compline",
            "For Wisdom and Devotion in Marriage",
            "Concluding Prayer at the Institution of a Rector",
            "For Witness in Marriage",
            "Thanksgiving for a Baptism",
            "During the Palm Procession",
            "The Commendation",
            "In the Morning",
            "For the Dead",
            "Solemn Collect for the Jews",
            "For the Renewal of Baptismal Vows",
            "Prayer for the Whole State of Christ's Church: for the Universal Church",
            "Prayer for the Whole State of Christ's Church: for Those in Trouble, Need, Sickness, or Other Adversity",
            "A Concluding Prayer for Good Friday",
            "For Relatives and Friends",
            "At the Time of Death",
            "For the Whole Church",
            "At the Reception of the Body",
            "Concluding Collect for the Prayers of the People for the Consecration of a Place of Worship",
            "Post Communion Prayer at the Institution of a Rector",
            "For a Sick Person When There Is Little Hope of Recovery",
            "The Gathering of God's People",
            "At a Cremation",
            "For the Newly Married and All Married Couples",
            "After a Burial",
            "For Growth in Love and Devotion in Marriage",
            "Requiem Aeternam",
            "Blessing of the Ashes",
            "Prayer for the Whole State of Christ's Church: for Our Leaders",
            "Post-Communion Prayer at a Burial",
            "Solemn Collect for the Holy Church",
            "For Courage and Reconciliation in Marriage",
            "For Those Made One Flesh in Marriage",
            "Prayer for the Whole State of Christ's Church: for the Departed",
            "For Belief and Trust",
            "For Healing",
            "Blessing of Water in the Font or Basin",
            "For a Home of Blessing and Peace in Marriage",
            "For the Ordination and Consecration of Bishops",
            "Prayer after Absolution",
            "Solemn Collect for the Clergy",
            "In Pain",
            "Prayer at the Laying on of Hands",
            "Blessing of the Pulpit",
            "Blessing of the Lectern",
            "Concluding Collect for the Consecration of a Place of Worship",
            "Blessing of Instruments and Bells",
            "Confession of Sin (Compline)",
            "Post-Communion Prayer at a Marriage",
            "Prayer for the Whole State of Christ's Church: Conclusion",
            "For the Baptized",
            "For the Parents",
            "For the Whole Communion of Saints",
            "Prayer for the Whole State of Christ's Church: for the Clergy",
            "Prayer for the Whole State of Christ's Church: for Those Who Proclaim the Gospel",
            "Concluding Collect at Ordinations",
            "Confession of Sin (Reconciliation of a Penitent)",
            "Thanksgiving for a Safe Childbirth",
            "Abraham's Sacrifice of Issac",
            "Solemn Collect for Those Preparing for Holy Baptism",
            "For Pardon and Peace",
        ]

        # Add to missing_collects query
        # We want missing_collects to include these even if spanish_text is NOT null?
        # User implies "still do not have collects".

        missing_collects = list(
            Collect.objects.filter(spanish_text__isnull=True).exclude(
                collect_type__uuid="b1c89797-8afd-4347-9583-3e79f3096680"
            )
        )

        # Fetch specific targets explicitly
        for t in specific_targets:
            matches = Collect.objects.filter(title__iexact=t)
            for m in matches:
                if m not in missing_collects:
                    missing_collects.append(m)

        # Map DB Title -> PDF Search Phrase
        title_search_map = {
            "A Prayer for Mission": "Prayer for Mission",
            "The General Thanksgiving": "General Thanksgiving",
            "A Prayer of St. John Chrysostom": "Prayer of St. John Chrysostom",
            "Confession of Sin (Daily Office)": "Almighty and most merciful Father",
            "At a Burial": "At the Burial",
            "For Those Who Mourn": "For those who mourn",
            "The Commendation": "The Commendation",
            "A Collect for Faith": "Collect for Faith",
            "For the Dead": "For the Departed",
            "The Apostles' Creed": "I believe in God, the Father almighty",
            # New Mappings from search
            "The Prayer of Humble Access": "We do not presume to come to this your table",
            "The Post Communion Prayer (Anglican Standard)": "Almighty and everliving God, we heartily thank you",
            "The Post Communion Prayer (Renewed Ancient)": "Heavenly Father, We thank you for feeding us",
            "For the Ordination of Deacons": "For the Ordination of Deacons",
            "For the Ordination of Priests": "For the Ordination of Priests",
            "The Consecration of a Bishop": "For the Consecration of a Bishop",
            "For the Ordination and Consecration of Bishops": "For the Ordination and Consecration of Bishops",
            "At a Burial of a Veteran of the Armed Forces.": "At the Burial of a Veteran",
            "Blessing of Instruments and Bells": "Blessing of Instruments and Bells",
            "The Three Young Men in the Furnace": "The Three Young Men in the Furnace",
            "Jonah and the Fish": "Jonah",
            "The Valley of Dry Bones": "The Valley of Dry Bones",
            "Prayer for a Vigil": "Prayer for a Vigil",
            "Compline Antiphon": "Guide us waking",
            "Blessing of the Font or Basin": "Blessing of the Font",
            "Thanksgiving for a Safe Childbirth": "Thanksgiving for a Safe Childbirth",  # Found in search? No.
            # "Safe Childbirth" missing in search. Maybe "Safe Delivery"?
            "Thanksgiving over Water": "Thanksgiving over Water",  # Baptism
            "Prayer for Baptismal Candidates": "Prayer for Baptismal Candidates",
            "Solemn Collects": "Dear People of God",  # Good Friday
            "Solemn Collect for the Holy Church": "For the Holy Church",
            "Solemn Collect for Our Bishops": "For our Bishops",
            "Solemn Collect for the Clergy": "For the Clergy",
            "Solemn Collect for Those Preparing for Holy Baptism": "For those preparing for Holy Baptism",
            "Solemn Collect for the Jews": "For the Jewish People",
            "Solemn Collect for Unbelievers": "For those who do not believe",
            "Solemn Collect against Hersey and Schism": "For protection against error",  # Guess?
            "Solemn Collect against Evil, Sickness, and Pestilence": "For protection against evil",  # Guess?
            "A Concluding Prayer for Good Friday": "Concluding Prayer",
            "For the Newly Married and All Married Couples": "For the Newly Married",
            "For Those Made One Flesh in Marriage": "For those made one flesh",
            "For Courage and Reconciliation in Marriage": "For Courage and Reconciliation",  # Missing in search?
            # "One Flesh" found. "Newly Married" found.
            "At the Palm Procession": "Palm Sunday",  # or "Liturgy of the Palms"
            "During the Palm Procession": "During the Procession",
            "Blessing of the Ashes": "Almighty God, you have created us out of the dust",  # Ash Wednesday
            "Requiem Aeternam": "Rest eternal",  # or "Eternal rest"
            "Prayer for the Great Plague of 1665": "In Time of Great Sickness",  # Try broad search
            "In the Time of any Common Plague or Sickness": "In Time of Sickness",
            "In Time of Great Sickness and Mortality": "In Time of Great Sickness",
        }

        # Group missing collects by Title
        missing_dict = {}  # Title -> [Collect objects]
        for c in missing_collects:
            t = c.title
            # We will search for ALL missing collects if possible.
            # But only those in our map or explicitly known?
            # Let's try to search for ALL missing titles.
            if t not in missing_dict:
                missing_dict[t] = []
            missing_dict[t].append(c)

        self.stdout.write(f"Targeting {len(missing_dict)} Unique Titles.")

        # 1. Find English Page & Order
        page_map = {}

        # Scan pages 15 to 700 (cover most rites)
        scan_range = range(15, 700)

        with pdfplumber.open(eng_path) as pdf:
            for i in scan_range:
                if i >= len(pdf.pages):
                    break
                page = pdf.pages[i]
                text = normalize(page.extract_text() or "")
                if not text:
                    continue

                # Check for titles
                for title in missing_dict.keys():
                    if title in page_map:
                        continue  # Already found

                    # Get search phrase
                    search_phrase = title_search_map.get(title, title)
                    norm_phrase = normalize(search_phrase)

                    # Regex for flexible whitespace
                    pattern = re.escape(norm_phrase).replace(r"\ ", r"\s+")

                    matches = [m.start() for m in re.finditer(pattern, text, re.IGNORECASE)]
                    if matches:
                        page_map[title] = {"page": i + 1, "index": 0}

        # Refine Order
        # Re-scan found pages to determine order
        page_contents = {}

        with pdfplumber.open(eng_path) as pdf:
            for title, info in page_map.items():
                p = info["page"]
                if p not in page_contents:
                    page_contents[p] = []
                    if p - 1 < len(pdf.pages):
                        text = normalize(pdf.pages[p - 1].extract_text() or "")

                        # Find all targeted titles on this page
                        # (Including titles we already found elsewhere? No, just titles in missing_dict)
                        # Wait, correct ranking requires knowing ALL collects on the page, even if some are already translated.
                        # But we don't know the titles of already translated collects easily.
                        # However, usually we are importing a whole block (e.g. Burial).
                        # If we assume missing_dict covers the missing ones, and we only care about those...
                        # Risk: If Page has [Existing, Missing], and we only search for Missing, we think Rank 0.
                        # But Spanish Page has [Existing, Missing]. Split gives 2 parts.
                        # If we think Rank 0, we take Existing text!
                        # Solution: Use "Amen" count heuristic.
                        pass

        # Use Amen Count Heuristic
        final_map = {}  # Title -> (Page, AmenCount)

        with pdfplumber.open(eng_path) as pdf:
            for title, info in page_map.items():
                p = info["page"]
                if p - 1 >= len(pdf.pages):
                    continue
                text = normalize(pdf.pages[p - 1].extract_text() or "")

                search_phrase = title_search_map.get(title, title)
                norm_phrase = normalize(search_phrase)
                pattern = re.escape(norm_phrase).replace(r"\ ", r"\s+")

                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    pos = match.start()
                    # Count Amens before pos
                    pre_text = text[:pos]
                    amen_count = len(re.findall(r"Amen", pre_text, re.IGNORECASE))
                    final_map[title] = (p, amen_count)

        self.stdout.write(f"Mappings found: {len(final_map)}")

        # 2. Extract from Spanish PDF
        with pdfplumber.open(spa_path) as pdf:
            updated_count = 0
            for title, (p, rank) in final_map.items():
                if title not in missing_dict:
                    continue

                if p > len(pdf.pages):
                    continue
                text = pdf.pages[p - 1].extract_text()
                if not text:
                    continue

                parts = re.split(r"Am[ée]n\.?", text, flags=re.IGNORECASE)

                if rank < len(parts) - 1:
                    collect_block = parts[rank].strip()

                    lines = collect_block.split("\n")
                    body_lines = []
                    prayer_started = False
                    starts = [
                        "Oh Dios",
                        "Dios",
                        "Señor",
                        "Padre",
                        "Concédenos",
                        "Te rogamos",
                        "Dirige",
                        "Acepta",
                        "Danos",
                    ]

                    for line in reversed(lines):
                        is_start = any(line.strip().startswith(s) for s in starts)
                        body_lines.insert(0, line)
                        if is_start:
                            prayer_started = True
                            break

                    if not prayer_started:
                        body_lines = lines[-6:]

                    full_body = " ".join(body_lines).strip()
                    full_body = re.sub(r"\s+", " ", full_body)

                    # Update ALL collects with this title
                    for collect_obj in missing_dict[title]:
                        collect_obj.spanish_text = f"<p>{full_body} Amén.</p>"
                        collect_obj.save()
                        updated_count += 1
                    self.stdout.write(f"Updated '{title}' (x{len(missing_dict[title])}) from Page {p}")
                else:
                    self.stdout.write(f"Rank mismatch for '{title}' on Page {p}: Rank {rank} vs {len(parts)-1} parts")

        self.stdout.write(f"Total updated: {updated_count}")
