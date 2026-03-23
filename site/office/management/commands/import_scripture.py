import re
import time

import scriptures
from django.core.management.base import BaseCommand

from bible.passage import Passage
from bible.sources import PassageNotFoundException
from churchcal.models import MassReading
from office.models import OfficeDay, Scripture

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


class Command(BaseCommand):
    help = "Import Bible translations for scripture passages"

    def add_arguments(self, parser):
        parser.add_argument(
            "--translations",
            nargs="+",
            default=[],
            help="Which translations to import (default: all)",
        )
        parser.add_argument(
            "--chinese",
            action="store_true",
            help="Import all Chinese translations (cuvs, cuv, sigao, znsigao)",
        )
        parser.add_argument(
            "--spanish",
            action="store_true",
            help="Import all Spanish translations (nvi, rv1960)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of passages to import (0 = all)",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.5,
            help="Sleep time between API calls in seconds",
        )

    def parse_passage(self, passage):
        try:
            references = scriptures.extract(passage)
            if not references:
                return None
            if len(references) == 1:
                return scriptures.reference_to_string(*references[0])
            return passage
        except:
            return None

    def break_apart_passages(self, original_passage):
        if "," not in original_passage:
            return [original_passage]
        book = re.sub(r"[^A-Za-z ]", "", original_passage)
        book = re.sub(r" +", " ", book.strip())
        chapter_verse = re.sub(r"[^0-9-,:]", "", original_passage)
        passages = chapter_verse.split(",")
        citations = []
        chapter = None
        for passage in passages:
            passage = passage.strip()
            if not passage:
                continue

            count = passage.count(":")
            if count > 1:
                citations.append(f"{book} {passage}")
            else:
                if ":" in passage:
                    try:
                        chapter, verses = passage.split(":")
                    except ValueError as e:
                        print("ERROR", original_passage)
                        raise (e)
                else:
                    verses = passage
                if chapter:
                    citations.append(f"{book} {chapter}:{verses}")
                else:
                    citations.append(f"{book} {verses}")
        return citations

    CJK_RE = re.compile(
        r"([\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u2e80-\u2eff\u3000-\u303f\uff00-\uffef])"
        r"\s+"
        r"([\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u2e80-\u2eff\u3000-\u303f\uff00-\uffef])"
    )
    CHINESE_TRANSLATIONS = {"cuv", "cuvs", "sigao", "znsigao"}

    @classmethod
    def _strip_cjk_spaces(cls, text):
        """Remove spaces between CJK characters inserted by BibleGateway."""
        if not text:
            return text
        text = cls.CJK_RE.sub(r"\1\2", text)
        text = cls.CJK_RE.sub(r"\1\2", text)
        return text

    def get_passages(self, passage, translation="esv"):
        final = []
        passages = self.break_apart_passages(passage)
        for p in passages:
            if "Psalms" not in p:
                p = self.parse_passage(p)
            if not p:
                return "-"
            try:
                result = Passage(p, source=translation).html
                final.append(result.strip())
                time.sleep(self.sleep_time)
            except PassageNotFoundException:
                return "-"
            except Exception as e:
                print(f"Error fetching {p} ({translation}): {e}")
                time.sleep(self.sleep_time * 4)
                return "-"
        text = " ".join(final)
        if translation in self.CHINESE_TRANSLATIONS:
            text = self._strip_cjk_spaces(text)
        return text

    def handle(self, *args, **options):
        # 1. Setup options
        limit = options["limit"]
        self.sleep_time = options["sleep"]
        translations = list(options["translations"])

        all_translations = [
            "esv",
            "rsv",
            "kjv",
            "nrsvce",
            "nabre",
            "niv",
            "nasb",
            "coverdale",
            "renewed_coverdale",
            "cuvs",
            "cuv",
            "sigao",
            "znsigao",
            "nvi",
            "rv1960",
        ]

        if options["chinese"]:
            translations.extend(["cuvs", "cuv", "sigao", "znsigao"])
        if options["spanish"]:
            translations.extend(["nvi", "rv1960"])

        if not translations:
            translations = all_translations

        # remove duplicates
        translations = list(set(translations))

        # 2. Ensure all Scripture objects exist for OfficeDay and MassReading
        self.stdout.write("Ensuring Scripture objects exist for all readings...")
        days = OfficeDay.objects.all()
        day_texts = [
            "mp_reading_1",
            "mp_reading_2",
            "ep_reading_1",
            "ep_reading_2",
            "mp_reading_1_abbreviated",
            "ep_reading_1_abbreviated",
        ]
        for day in days:
            for text in day_texts:
                passage = getattr(day, text)
                if passage:
                    Scripture.objects.get_or_create(passage=passage)

        mass_readings = MassReading.objects.all()
        mass_texts = ["long_citation", "short_citation"]
        for reading in mass_readings:
            for text in mass_texts:
                passage = getattr(reading, text)
                if passage:
                    Scripture.objects.get_or_create(passage=passage)

        scriptures = Scripture.objects.all()
        total = scriptures.count()
        imported = 0
        errors = 0
        skipped = 0

        self.stdout.write(f"Processing {total} passages for translations: {', '.join(translations)}")

        for i, scripture in enumerate(scriptures):
            if limit and imported >= limit:
                break

            passage = scripture.passage
            changed = False

            for translation in translations:
                existing = getattr(scripture, translation)
                if existing and existing.strip() not in ("", "-"):
                    continue  # Already has data

                try:
                    text = self.get_passages(passage, translation)
                    if text and text.strip() and text.strip() != "-":
                        setattr(scripture, translation, text.strip())
                        changed = True
                        self.stdout.write(f"  [{i+1}/{total}] {passage} ({translation}): OK")
                    else:
                        setattr(scripture, translation, "-")
                        changed = True
                        self.stdout.write(f"  [{i+1}/{total}] {passage} ({translation}): empty")
                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  [{i+1}/{total}] {passage} ({translation}): ERROR - {e}")

            if changed:
                scripture.save()
                imported += 1
            else:
                skipped += 1

            if (i + 1) % 50 == 0:
                self.stdout.write(
                    f"Progress: {i+1}/{total} processed, {imported} imported, {skipped} skipped, {errors} errors"
                )

        # 3. Handle Apocrypha (KJV -> av fallback)
        if "kjv" in translations:
            self.stdout.write("Checking for missing KJV passages that might need the 'av' fallback...")
            needed_for_apocrypha = Scripture.objects.filter(kjv="-").all()
            for scripture in needed_for_apocrypha:
                try:
                    text = self.get_passages(scripture.passage, "av")
                    if text and text.strip() and text.strip() != "-":
                        scripture.kjv = text.strip()
                        scripture.save()
                        self.stdout.write(f"  [Apocrypha] {scripture.passage} (kjv fallback to av): OK")
                except Exception as e:
                    self.stderr.write(f"  [Apocrypha] {scripture.passage} (kjv fallback to av): ERROR - {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! {imported} imported, {skipped} skipped, {errors} errors out of {total} passages."
            )
        )
