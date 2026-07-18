from datetime import timedelta

import kronos
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory
from django.urls import resolve
from django.utils import timezone

from office.audio import set_audio_pipeline
from office.audio.pipeline import PIPELINE_GEMINI, PIPELINE_LEGACY, PIPELINE_V2, VALID_PIPELINES


@kronos.register("55 9 * * *")
class Command(BaseCommand):
    help = "Pre-warm office audio files for upcoming days (legacy / v2 / gemini)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pipeline",
            choices=["active", "legacy", "v2", "gemini", "both", "all"],
            default="active",
            help=(
                "Which audio pipeline to pre-warm. "
                "'active' uses OFFICE_AUDIO_PIPELINE; 'both' = legacy+v2; 'all' = legacy+v2+gemini."
            ),
        )
        parser.add_argument(
            "--days",
            type=int,
            default=8,
            help="Number of days to warm starting today (default: 8).",
        )
        parser.add_argument(
            "--no-yesterday",
            action="store_true",
            help="Do not also warm yesterday.",
        )
        parser.add_argument(
            "--batch",
            nargs="?",
            const="sync",
            choices=["sync", "submit", "fetch"],
            default=None,
            help=(
                "Use the Gemini Batch API (roughly half price, asynchronous). Only affects the "
                "'gemini' pipeline. 'sync' (default when the flag is given) submits, waits, and "
                "assembles in one run. 'submit' queues batch jobs (persisted to the DB) and exits. "
                "'fetch' polls previously submitted jobs and writes finished clips. Suitable for "
                "scheduled/advance runs, not on-demand requests."
            ),
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            raise CommandError("--days must be at least 1")

        batch_mode = options.get("batch")  # None | "sync" | "submit" | "fetch"
        include_yesterday = not options["no_yesterday"]

        # "fetch" is pipeline-independent: it just drains previously submitted jobs.
        if batch_mode == "fetch":
            set_audio_pipeline(PIPELINE_GEMINI)
            try:
                self._batch_fetch()
            finally:
                set_audio_pipeline(None)
            return

        pipeline_option = options.get("pipeline") or "active"
        if pipeline_option == "active":
            pipelines = [getattr(settings, "OFFICE_AUDIO_PIPELINE", PIPELINE_V2)]
        elif pipeline_option == "both":
            pipelines = [PIPELINE_LEGACY, PIPELINE_V2]
        elif pipeline_option == "all":
            pipelines = [PIPELINE_LEGACY, PIPELINE_V2, PIPELINE_GEMINI]
        else:
            pipelines = [pipeline_option]

        pipelines = [str(p).strip().lower() for p in pipelines]
        for pipeline in pipelines:
            if pipeline not in VALID_PIPELINES:
                self.stderr.write(f"Skipping invalid pipeline: {pipeline}")
                continue
            self.stdout.write(f"Pre-warming audio pipeline: {pipeline}")
            set_audio_pipeline(pipeline)
            try:
                if batch_mode and pipeline != PIPELINE_GEMINI:
                    self.stdout.write(f"  (batch not applicable to '{pipeline}'; warming synchronously)")
                    self._warm_range(days=days, include_yesterday=include_yesterday)
                elif batch_mode == "submit":
                    self._batch_submit(days=days, include_yesterday=include_yesterday)
                elif batch_mode == "sync":
                    self._warm_range_via_batch(days=days, include_yesterday=include_yesterday)
                else:
                    self._warm_range(days=days, include_yesterday=include_yesterday)
            finally:
                set_audio_pipeline(None)

    def _collect_batch_chunks(self, days, include_yesterday):
        """Phase 1 shared by sync/submit: dry-run render to discover cache misses.

        Every office renders as "unavailable" here by design, so the expected
        per-office generation errors are silenced.
        """
        import logging

        from office.audio.gemini import collecting_batch_chunks

        v2_logger = logging.getLogger("office.audio.v2")
        index_logger = logging.getLogger("office.api.views.index")
        previous_levels = (v2_logger.level, index_logger.level)
        v2_logger.setLevel(logging.CRITICAL)
        index_logger.setLevel(logging.CRITICAL)
        try:
            with collecting_batch_chunks() as collector:
                self._warm_range(days=days, include_yesterday=include_yesterday, quiet=True)
            return collector.chunks()
        finally:
            v2_logger.setLevel(previous_levels[0])
            index_logger.setLevel(previous_levels[1])

    def _batch_submit(self, days, include_yesterday):
        """Queue Gemini batch jobs for all cache-miss clips and persist them."""
        from office.audio.gemini_batch import submit_chunks
        from office.models import AudioBatchJob

        self.stdout.write("Batch submit: collecting cache-miss clips...")
        chunks = self._collect_batch_chunks(days=days, include_yesterday=include_yesterday)
        if not chunks:
            self.stdout.write("  nothing to synthesize (cache already warm)")
            return

        self.stdout.write(f"Batch submit: sending {len(chunks)} unique clip(s) to the Batch API...")
        submitted = submit_chunks(chunks)
        for record in submitted:
            AudioBatchJob.objects.update_or_create(
                job_name=record["job_name"],
                defaults={
                    "model_name": record.get("model_name", ""),
                    "status": AudioBatchJob.STATUS_PENDING,
                    "chunks": record["chunks"],
                    "written": 0,
                    "failed": 0,
                    "last_state": "",
                    "detail": "",
                    "completed_at": None,
                },
            )
        clip_count = sum(len(record["chunks"]) for record in submitted)
        self.stdout.write(
            f"  submitted {len(submitted)} job(s) covering {clip_count} clip(s); "
            "run `update_audio_files --batch fetch` later to retrieve them"
        )

    def _batch_fetch(self):
        """Poll pending batch jobs and write finished clips to the cache."""
        from office.audio.gemini_batch import fetch_job
        from office.models import AudioBatchJob

        pending = list(AudioBatchJob.objects.filter(status=AudioBatchJob.STATUS_PENDING))
        if not pending:
            self.stdout.write("Batch fetch: no pending jobs")
            return

        self.stdout.write(f"Batch fetch: checking {len(pending)} pending job(s)...")
        still_pending = 0
        for job in pending:
            try:
                result = fetch_job(job.job_name, job.chunks or [])
            except Exception as exc:  # noqa: BLE001 — keep draining other jobs
                self.stderr.write(f"  {job.job_name}: error polling ({exc})")
                continue

            job.last_state = result["state"]
            if not result["terminal"]:
                still_pending += 1
                job.save(update_fields=["last_state", "updated"])
                continue

            job.written = result["written"]
            job.failed = result["failed"]
            job.status = AudioBatchJob.STATUS_SUCCEEDED if result["succeeded"] else AudioBatchJob.STATUS_FAILED
            job.completed_at = timezone.now()
            job.save()
            self.stdout.write(
                f"  {job.job_name}: {result['state']} " f"(written={result['written']} failed={result['failed']})"
            )

        self.stdout.write(f"Batch fetch: {still_pending} job(s) still running")
        if still_pending == 0:
            self.stdout.write("All jobs finished. Run a normal warm to assemble offices from the cached clips.")

    def _warm_range_via_batch(self, days, include_yesterday):
        """Three-phase Gemini pre-warm: collect cache misses, batch-synthesize
        them cheaply, then assemble (real-time synthesizing any stragglers)."""
        import logging

        from office.audio.gemini import collecting_batch_chunks
        from office.audio.gemini_batch import run_batch_synthesis

        # Phase 1: dry-run render to discover which clips are missing. Every office
        # renders as "unavailable" here by design, so silence the expected errors.
        self.stdout.write("Batch phase 1/3: collecting cache-miss clips...")
        v2_logger = logging.getLogger("office.audio.v2")
        index_logger = logging.getLogger("office.api.views.index")
        previous_levels = (v2_logger.level, index_logger.level)
        v2_logger.setLevel(logging.CRITICAL)
        index_logger.setLevel(logging.CRITICAL)
        try:
            with collecting_batch_chunks() as collector:
                self._warm_range(days=days, include_yesterday=include_yesterday, quiet=True)
            chunks = collector.chunks()
        finally:
            v2_logger.setLevel(previous_levels[0])
            index_logger.setLevel(previous_levels[1])

        self.stdout.write(f"Batch phase 2/3: synthesizing {len(chunks)} unique clip(s) via Batch API...")
        summary = run_batch_synthesis(chunks)
        self.stdout.write(
            f"  batch results: requested={summary['requested']} "
            f"written={summary['written']} failed={summary['failed']}"
        )

        # Phase 3: normal render. Batch-written clips are cache hits; anything the
        # batch missed is synthesized in real time so the offices are complete.
        self.stdout.write("Batch phase 3/3: assembling offices...")
        self._warm_range(days=days, include_yesterday=include_yesterday)

    @staticmethod
    def _date_list(now, days, include_yesterday):
        dates = [now + timedelta(days=i) for i in range(days)]
        if include_yesterday:
            dates.insert(0, now - timedelta(days=1))
        return dates

    def _warm_range(self, days=8, include_yesterday=True, quiet=False):
        now = timezone.now()
        date_list = self._date_list(now, days, include_yesterday)

        for day in date_list:
            offices = [
                "office/morning_prayer",
                "office/midday_prayer",
                "office/evening_prayer",
                "office/compline",
                "family/morning_prayer",
                "family/midday_prayer",
                "family/early_evening_prayer",
                "family/close_of_day_prayer",
            ]

            for office in offices:
                base_url = f"/api/v1/{office}/{day.strftime('%Y-%m-%d')}"

                query_params = {
                    "language_style": "contemporary",
                    "psalm_translation": "contemporary",
                    "bible_translation": "esv",
                    "display_language": "english",
                    "psalter": "60",
                    "reading_cycle": "1",
                    "reading_length": "full",
                    "reading_audio": "off",
                    "canticle_rotation": "1979",
                    "psalm_style": "whole_verse",
                    "lectionary": "daily-office-readings",
                    "confession": "long-on-fast",
                    "absolution": "lay",
                    "morning_prayer_invitatory": "invitatory_traditional",
                    "reading_headings": "off",
                    "language_style_for_our_father": "traditional",
                    "national_holidays": "all",
                    "suffrages": "rotating",
                    "collects": "rotating",
                    "mp_great_litany": "mp_litany_on",
                    "ep_great_litany": "ep_litany_on",
                    "general_thanksgiving": "on",
                    "chrysostom": "on",
                    "grace": "rotating",
                    "o_antiphons": "literal",
                    "family_readings": "brief",
                    "family_reading_audio": "off",
                    "family_collect": "time_of_day",
                    "family-opening-sentence": "family-opening-sentence-fixed",
                    "family-creed": "family-creed-yes",
                    "extra_collects": "",
                    "include_audio_links": "true",
                }

                contemporary_and_traditional = [
                    {
                        "language_style": "contemporary",
                        "psalm_translation": "contemporary",
                        "bible_translation": "esv",
                        "language_style_for_our_father": "contemporary",
                        "display_language": "english",
                    },
                    {
                        "language_style": "traditional",
                        "psalm_translation": "traditional",
                        "bible_translation": "kjv",
                        "language_style_for_our_father": "traditional",
                        "display_language": "english",
                    },
                ]

                for style in contemporary_and_traditional:
                    new_params = query_params.copy()
                    new_params |= style
                    more_changes = [
                        {"psalter": "30"},
                        {"canticle_rotation": "default"},
                        {"canticle_rotation": "2011"},
                        {"psalm_style": "half_verse"},
                        {"psalm_style": "unison"},
                        {"lectionary": "mass-readings"},
                        {"absolution": "priest"},
                        {"morning_prayer_invitatory": "invitatory_jubilate_on_feasts"},
                        {"morning_prayer_invitatory": "celebratory_always"},
                        {"morning_prayer_invitatory": "invitatory_rotating"},
                        {"reading_length": "abbreviated"},
                    ]
                    for change in more_changes:
                        newest_params = new_params.copy()
                        newest_params |= change

                        factory = RequestFactory()
                        request = factory.get(base_url, data=newest_params)
                        if not quiet:
                            self.stdout.write(f"{base_url} {newest_params}")
                        match = resolve(base_url)
                        response = match.func(request, *match.args, **match.kwargs)

                        if hasattr(response, "render") and callable(response.render):
                            response = response.render()

                        if not quiet:
                            self.stdout.write(str(response.status_code))
