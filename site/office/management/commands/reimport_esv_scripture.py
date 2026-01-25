"""
Management command to reimport ESV scripture content from XML files.

This command:
1. Selects all instances of the Scripture model
2. Loops through each and uses the ESV XML adapter
3. Replaces the ESV field content (including empty, null, or "-")
4. Handles errors prominently
5. Includes Apocrypha citations
6. Does not touch other translation fields
"""

import traceback

from django.core.management.base import BaseCommand
from django.db import transaction

from bible.esv_xml_adapter import ESVXMLAdapter
from bible.sources import PassageNotFoundException
from office.models import Scripture


class Command(BaseCommand):
    help = "Reimport ESV scripture content from XML files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without saving changes to database",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit number of scriptures to process (for testing)",
        )
        parser.add_argument(
            "--passage",
            type=str,
            help="Process only a specific passage (for testing)",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        limit = options.get("limit")
        specific_passage = options.get("passage")

        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("ESV Scripture Reimport from XML Files"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be saved"))

        # Get all Scripture instances
        if specific_passage:
            scriptures = Scripture.objects.filter(passage=specific_passage)
            self.stdout.write(f"Processing specific passage: {specific_passage}")
        else:
            scriptures = Scripture.objects.all()
            if limit:
                scriptures = scriptures[:limit]
                self.stdout.write(f"Processing first {limit} scriptures")
            else:
                self.stdout.write(f"Processing all {scriptures.count()} scriptures")

        self.stdout.write("")

        # Counters for statistics
        total_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        errors = []

        # Process each scripture
        for scripture in scriptures:
            total_count += 1
            passage = scripture.passage

            if not passage or passage.strip() == "":
                self.stdout.write(self.style.WARNING(f"[{total_count}] Skipping empty passage"))
                skipped_count += 1
                continue

            try:
                self.stdout.write(f"[{total_count}] Processing: {passage}")

                # Use ESV XML adapter to get the passage
                adapter = ESVXMLAdapter(passage, "esv")
                html = adapter.get_html()

                if not html or html.strip() == "":
                    self.stdout.write(self.style.WARNING(f"  → Empty HTML returned for {passage}"))
                    skipped_count += 1
                    continue

                # Update the ESV field
                old_value = scripture.esv
                scripture.esv = html

                # Show preview of changes
                if old_value != html:
                    self.stdout.write(f"  → Updated ({len(html)} characters)")
                    if len(html) > 200:
                        preview = html[:200] + "..."
                    else:
                        preview = html
                    self.stdout.write(f"  → Preview: {preview}")
                else:
                    self.stdout.write("  → No change needed")
                    skipped_count += 1
                    continue

                # Save unless dry run
                if not dry_run:
                    scripture.save()
                    self.stdout.write(self.style.SUCCESS(f"  → Saved"))
                else:
                    self.stdout.write(self.style.WARNING(f"  → Would save (dry run)"))

                updated_count += 1

            except PassageNotFoundException as e:
                error_msg = f"[{total_count}] ERROR - Passage not found: {passage} - {str(e)}"
                self.stdout.write(self.style.ERROR("*" * 70))
                self.stdout.write(self.style.ERROR(error_msg))
                self.stdout.write(self.style.ERROR("*" * 70))
                errors.append((passage, str(e)))
                error_count += 1

            except Exception as e:
                error_msg = f"[{total_count}] ERROR - Unexpected error for {passage}: {str(e)}"
                self.stdout.write(self.style.ERROR("*" * 70))
                self.stdout.write(self.style.ERROR(error_msg))
                self.stdout.write(self.style.ERROR("*" * 70))

                # Print full traceback for debugging
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

                errors.append((passage, str(e)))
                error_count += 1

        # Print summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(f"Total processed: {total_count}")
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
        self.stdout.write(self.style.WARNING(f"Skipped: {skipped_count}"))
        self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))

        if errors:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("ERRORS ENCOUNTERED:"))
            self.stdout.write(self.style.ERROR("-" * 70))
            for passage, error in errors:
                self.stdout.write(self.style.ERROR(f"  {passage}: {error}"))

        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("DRY RUN - No changes were saved to the database"))

        self.stdout.write("")

        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f"Command completed with {error_count} error(s). Please review the errors above.")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Command completed successfully!"))
