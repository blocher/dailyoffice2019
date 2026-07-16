from django.contrib.postgres.fields import ArrayField
from django.core.management.base import BaseCommand
from django.db import models

from churchcal.ce_bce_replacement import replace_ce_bce_in_text
from churchcal.models import Commemoration


class Command(BaseCommand):
    help = (
        "Replace CE/BCE year markers with AD/BC in all Commemoration fields starting with 'ai_'. "
        "Runs in dry-run mode by default; pass --execute to save changes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Save replacements to the database. Without this flag, only shows what would change.",
        )

    def handle(self, *args, **options):
        is_dry_run = not options["execute"]
        commemorations = Commemoration.objects.all().order_by("name")

        if is_dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode. No changes will be saved."))
        else:
            self.stdout.write(self.style.ERROR("Running in EXECUTE mode. Changes WILL be saved."))

        total_commemorations_changed = 0
        total_fields_changed = 0
        total_replacements = 0

        for commemoration in commemorations:
            field_updates = self._collect_field_updates(commemoration)
            if not field_updates:
                continue

            total_commemorations_changed += 1
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING(f"{commemoration.name} ({commemoration.uuid})"))

            for field_name, replacements, new_value in field_updates:
                total_fields_changed += 1
                total_replacements += len(replacements)
                self.stdout.write(f"  {field_name}:")
                for replacement in replacements:
                    self.stdout.write(f'    "{replacement.original}" -> "{replacement.replacement}"')
                    if is_dry_run:
                        self.stdout.write(f"      before: {replacement.context_before}")
                        self.stdout.write(f"      after:  {replacement.context_after}")

                if not is_dry_run:
                    setattr(commemoration, field_name, new_value)

            if not is_dry_run:
                commemoration.save(update_fields=[field_name for field_name, _, _ in field_updates])

        self.stdout.write("")
        self.stdout.write("=" * 40)
        self.stdout.write(f"Commemorations scanned: {commemorations.count()}")
        self.stdout.write(f"Commemorations with changes: {total_commemorations_changed}")
        self.stdout.write(f"Fields updated: {total_fields_changed}")
        self.stdout.write(f"Total replacements: {total_replacements}")

        if is_dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run. Run with --execute to apply changes."))

    def _collect_field_updates(self, commemoration):
        updates = []

        for field in commemoration._meta.get_fields():
            if not field.name.startswith("ai_"):
                continue
            if not getattr(field, "concrete", False):
                continue

            if isinstance(field, ArrayField):
                update = self._update_array_field(commemoration, field.name)
            elif isinstance(field, (models.TextField, models.CharField, models.URLField)):
                update = self._update_text_field(commemoration, field.name)
            else:
                continue

            if update:
                updates.append(update)

        return updates

    def _update_text_field(self, commemoration, field_name):
        value = getattr(commemoration, field_name)
        if not value:
            return None

        new_value, replacements = replace_ce_bce_in_text(value)
        if new_value == value:
            return None

        return field_name, replacements, new_value

    def _update_array_field(self, commemoration, field_name):
        values = getattr(commemoration, field_name)
        if not values:
            return None

        new_values = []
        replacements = []
        changed = False

        for item in values:
            if not isinstance(item, str) or not item:
                new_values.append(item)
                continue

            new_item, item_replacements = replace_ce_bce_in_text(item)
            new_values.append(new_item)
            if item_replacements:
                changed = True
                replacements.extend(item_replacements)

        if not changed:
            return None

        return field_name, replacements, new_values
