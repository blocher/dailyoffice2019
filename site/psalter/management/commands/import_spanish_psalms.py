import re
import time

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from bible.passage import Passage
from bible.sources import PassageNotFoundException
from psalter.models import Psalm, PsalmVerse


class Command(BaseCommand):
    help = "Import Spanish (NVI) psalm text from BibleGateway into PsalmVerse.first_half_spanish/second_half_spanish"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start", type=int, default=1, help="Starting psalm number (default: 1)"
        )
        parser.add_argument(
            "--end", type=int, default=150, help="Ending psalm number (default: 150)"
        )
        parser.add_argument(
            "--force", action="store_true", help="Overwrite existing Spanish text"
        )

    def handle(self, *args, **options):
        start = options["start"]
        end = options["end"]
        force = options["force"]

        for psalm_num in range(start, end + 1):
            psalm = Psalm.objects.filter(number=psalm_num).first()
            if not psalm:
                self.stdout.write(f"Psalm {psalm_num}: not found in database, skipping")
                continue

            verses = PsalmVerse.objects.filter(psalm=psalm).order_by("number")
            if not force and verses.filter(first_half_spanish__isnull=False).exclude(first_half_spanish="").exists():
                self.stdout.write(f"Psalm {psalm_num}: already has Spanish text, skipping (use --force to overwrite)")
                continue

            self.stdout.write(f"Psalm {psalm_num}: fetching from BibleGateway (NVI)...")
            try:
                passage = Passage(f"Psalm {psalm_num}", source="nvi")
                html = passage.html
                if not html or html.strip() in ["", "-"]:
                    self.stdout.write(f"  No text returned, skipping")
                    continue
            except PassageNotFoundException:
                self.stdout.write(f"  Passage not found, skipping")
                time.sleep(1)
                continue
            except Exception as e:
                self.stdout.write(f"  Error: {e}")
                time.sleep(2)
                continue

            # Parse the HTML to extract verse text
            soup = BeautifulSoup(html, "html.parser")

            # Remove footnotes and cross-references
            for sup in soup.find_all("sup", class_="footnote"):
                sup.decompose()
            for sup in soup.find_all("sup", class_="crossreference"):
                sup.decompose()
            for div in soup.find_all("div", class_="footnotes"):
                div.decompose()
            for div in soup.find_all("div", class_="crossrefs"):
                div.decompose()

            # Extract verses from BibleGateway HTML
            # BG uses <span class="text Ps-N-V"> with <sup class="versenum">N</sup> inside
            verse_texts = {}

            # Method: get full text, then split by verse numbers
            # First remove all heading elements
            for h in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
                h.decompose()
            for span in soup.find_all("span", class_="chapternum"):
                span.replace_with("||VERSE_1||")

            # Get the passage div content
            passage_div = soup.find("div", class_="passage-text") or soup
            full_text = ""
            for p in passage_div.find_all("p"):
                p_text = ""
                for child in p.children:
                    if hasattr(child, "name") and child.name == "sup" and "versenum" in (child.get("class") or []):
                        num = child.get_text().strip().replace("\xa0", "")
                        p_text += f"||VERSE_{num}||"
                    elif hasattr(child, "get_text"):
                        # Check for nested versenum
                        for vn in child.find_all("sup", class_="versenum") if hasattr(child, "find_all") else []:
                            num = vn.get_text().strip().replace("\xa0", "")
                            vn.replace_with(f"||VERSE_{num}||")
                        for cn in child.find_all("span", class_="chapternum") if hasattr(child, "find_all") else []:
                            cn.replace_with("||VERSE_1||")
                        p_text += child.get_text()
                    else:
                        p_text += str(child)
                full_text += p_text + " "

            # Parse out verses from markers
            full_text = re.sub(r"\s+", " ", full_text).strip()
            parts = re.split(r"\|\|VERSE_(\d+)\|\|", full_text)

            # parts[0] is text before first verse marker (usually empty or title)
            # parts[1] = verse num, parts[2] = text, parts[3] = verse num, parts[4] = text, etc.
            for i in range(1, len(parts) - 1, 2):
                try:
                    verse_num = int(parts[i])
                    verse_text = parts[i + 1].strip()
                    if verse_text:
                        verse_texts[verse_num] = verse_text
                except (ValueError, IndexError):
                    continue

            if not verse_texts:
                self.stdout.write(f"  Could not parse verses")
                time.sleep(1)
                continue

            # Update PsalmVerse records
            updated = 0
            for verse in verses:
                verse_text = verse_texts.get(verse.number, "")
                if not verse_text:
                    continue

                # Split into two halves at a natural midpoint
                # Try splitting at semicolon, comma, or midpoint
                first_half, second_half = self._split_verse(verse_text)

                verse.first_half_spanish = first_half
                verse.second_half_spanish = second_half
                verse.save()
                updated += 1

            self.stdout.write(f"  Updated {updated}/{verses.count()} verses")
            time.sleep(1)

    @staticmethod
    def _split_verse(text):
        """Split a verse into two halves for antiphonal reading."""
        text = text.strip()

        # If there's a semicolon, split there
        if ";" in text:
            parts = text.split(";", 1)
            return parts[0].strip() + ";", parts[1].strip()

        # If there's a colon followed by text (not a verse reference), split there
        colon_match = re.search(r"(?<=[a-záéíóúñü]):\s", text, re.IGNORECASE)
        if colon_match:
            pos = colon_match.start() + 1
            return text[:pos].strip(), text[pos:].strip()

        # Otherwise split at the midpoint comma
        commas = [m.start() for m in re.finditer(r",\s", text)]
        if commas:
            mid = len(text) // 2
            best = min(commas, key=lambda x: abs(x - mid))
            return text[: best + 1].strip(), text[best + 1 :].strip()

        # Last resort: split at midpoint space
        mid = len(text) // 2
        space_before = text.rfind(" ", 0, mid)
        space_after = text.find(" ", mid)
        if space_after != -1:
            split_pos = space_after
        elif space_before != -1:
            split_pos = space_before
        else:
            return text, ""

        return text[:split_pos].strip(), text[split_pos:].strip()
