import statistics
from datetime import UTC, datetime, time, timedelta

import bugsnag
import kronos
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Min, Q, Sum
from django.utils import timezone

from office.models import TTSGeneration

USAGE_URL = "https://api.elevenlabs.io/v1/usage/character-stats"
# Billed credits per character we submit vary by model and plan, so each day is
# judged against the ratio of the days before it rather than a fixed rate.
BASELINE_DAYS = 7
MIN_BASELINE_DAYS = 3
RATIO_TOLERANCE = 1.25


class SpendAlert(Exception):
    """ElevenLabs billed for more audio than the cache accounts for."""


# After the overnight warming runs and well before most listeners.
@kronos.register("0 9 * * *")
class Command(BaseCommand):
    help = "Compare yesterday's ElevenLabs bill with the audio we recorded generating, and alert on waste."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Day to check (YYYY-MM-DD, server time). Default: yesterday.")

    def handle(self, *args, **options):
        api_key = getattr(settings, "ELEVENLABS_API_KEY", "")
        if not api_key:
            raise CommandError("ELEVENLABS_API_KEY is not configured.")
        today = timezone.localdate()
        day = datetime.strptime(options["date"], "%Y-%m-%d").date() if options["date"] else today - timedelta(days=1)
        days = [day - timedelta(days=offset) for offset in range(BASELINE_DAYS, -1, -1)]
        billed = self.billed_by_day(api_key, days)
        ledger_start = TTSGeneration.objects.filter(provider="elevenlabs").aggregate(first=Min("created"))["first"]

        def recorded(d):
            start, end = self.bounds(d)
            totals = TTSGeneration.objects.filter(
                provider="elevenlabs", created__gte=start, created__lt=end
            ).aggregate(total=Sum("characters"), repeated=Sum("characters", filter=Q(regenerated=True)))
            return totals["total"] or 0, totals["repeated"] or 0

        def fully_recorded(d):
            return ledger_start is not None and ledger_start <= self.bounds(d)[0]

        characters, regenerated = recorded(day)
        credits = billed[day]
        ratio = credits / characters if characters else None
        self.stdout.write(
            f"{day}: billed {credits:,} credits; recorded {characters:,} characters "
            f"({regenerated:,} regenerated)" + (f"; {ratio:.2f} credits per character" if ratio else "")
        )

        problems = []
        if regenerated:
            problems.append(f"{regenerated:,} characters of audio that was already generated were paid for again")
        budget = getattr(settings, "ELEVENLABS_DAILY_CREDIT_BUDGET", 0)
        if budget and credits > budget:
            problems.append(f"{credits:,} credits is over the daily budget of {budget:,}")
        if fully_recorded(day):
            baseline = []
            for d in days[:-1]:
                previous_characters, _ = recorded(d)
                if fully_recorded(d) and previous_characters and billed[d]:
                    baseline.append(billed[d] / previous_characters)
            if characters == 0 and credits:
                problems.append(f"{credits:,} credits were billed but no generation was recorded")
            elif ratio and len(baseline) >= MIN_BASELINE_DAYS:
                expected = statistics.median(baseline)
                self.stdout.write(f"Baseline: {expected:.2f} credits per character over {len(baseline)} days")
                if ratio > expected * RATIO_TOLERANCE:
                    unexplained = round(credits - characters * expected)
                    problems.append(
                        f"about {unexplained:,} credits are not explained by recorded generations "
                        f"({ratio:.2f} credits per character against a usual {expected:.2f})"
                    )
        else:
            self.stdout.write("Generations were not recorded for the whole day; skipping the ratio check.")

        for problem in problems:
            self.stdout.write(self.style.WARNING(problem))
        if problems:
            bugsnag.notify(
                SpendAlert("; ".join(problems)),
                severity="error",
                context="tts_spend",
                metadata={
                    "spend": {
                        "date": str(day),
                        "billed_credits": credits,
                        "recorded_characters": characters,
                        "regenerated_characters": regenerated,
                    }
                },
            )

    @staticmethod
    def bounds(day):
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.combine(day, time.min), tz)
        return start, timezone.make_aware(datetime.combine(day + timedelta(days=1), time.min), tz)

    def billed_by_day(self, api_key, days):
        """Credits per local day; hourly buckets, since the API's days are UTC days."""
        start, end = self.bounds(days[0])[0], self.bounds(days[-1])[1]
        response = requests.get(
            USAGE_URL,
            headers={"xi-api-key": api_key},
            params={
                "start_unix": int(start.timestamp() * 1000),
                "end_unix": int(end.timestamp() * 1000),
                "aggregation_interval": "hour",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        totals = {d: 0 for d in days}
        for index, stamp in enumerate(data.get("time", [])):
            local_day = timezone.localtime(datetime.fromtimestamp(stamp / 1000, tz=UTC)).date()
            if local_day in totals:
                totals[local_day] += round(sum(series[index] for series in data.get("usage", {}).values()))
        return totals
