"""The podcast feeds: what each one is, how it is built, and how it is described.

Every office podcast is the same generated audio as the in-app player, built
with one fixed set of settings, so that listeners hear what the site shows
when they follow along with the episode's link. Changing a feed's settings
changes future episodes only; published episodes are never rebuilt.

Feed slugs appear in public feed and episode URLs. Never rename one.
"""

from dataclasses import dataclass, field
from urllib.parse import urlencode

SITE_URL = "https://www.dailyoffice2019.com"
LANDING_PAGE_URL = f"{SITE_URL}/podcasts"
SUPPORT_URL = "https://ko-fi.com/dailyoffice"
OWNER_NAME = "The Daily Office"
OWNER_EMAIL = "feedback@dailyoffice2019.com"
AUTHOR = "The Daily Office"
COPYRIGHT = "The Daily Office (dailyoffice2019.com). Scripture from the ESV® and the KJV; see each episode."
LANGUAGE = "en-us"
CATEGORY = ("Religion & Spirituality", "Christianity")

# The settings of the two families of office podcasts, exactly as a listener
# would set them on the site. Kept as an ordered list so the "pray along" links
# carry them in a stable, readable order.
CONTEMPORARY_SETTINGS = {
    "display_language": "english",
    "language_style": "contemporary",
    "psalm_translation": "contemporary",
    "bible_translation": "esv",
    "psalter": "60",
    "reading_cycle": "1",
    "reading_length": "full",
    "reading_audio": "on",
    "canticle_rotation": "default",
    "apocrypha_readings": "appointed",
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
    "mp_great_litany": "mp_litany_w_f_s",
    "commemoration_info": "full_hagiography",
    "ep_great_litany": "ep_litany_off",
    "great_litany_ending": "supplication",
    "general_thanksgiving": "on",
    "chrysostom": "on",
    "grace": "rotating",
    "o_antiphons": "literal",
    "family_readings": "brief",
    "family_reading_audio": "off",
    "family_collect": "time_of_day",
    "family-opening-sentence": "family-opening-sentence-fixed",
    "family-creed": "family-creed-yes",
}

TRADITIONAL_SETTINGS = {
    **CONTEMPORARY_SETTINGS,
    "language_style": "traditional",
    "psalm_translation": "traditional",
    "bible_translation": "kjv",
}

# The readings podcasts' choices on the Readings page, in the same two families.
READINGS_SETTINGS = {"translation": "esv", "psalms": "contemporary", "style": "whole_verse", "psalter": "60"}
TRADITIONAL_READINGS_SETTINGS = {**READINGS_SETTINGS, "translation": "kjv", "psalms": "traditional"}

CONTEMPORARY = "contemporary"
TRADITIONAL = "traditional"

SYNTHESIZED_VOICE_NOTE = (
    "Read with synthesized (AI) voices, produced by the free Daily Office website and app, "
    "so a fresh episode is ready every day of the year."
)


@dataclass(frozen=True)
class PodcastFeed:
    slug: str
    title: str
    subtitle: str
    description: str
    group: str  # "daily-office", "family", or "readings": landing-page sections
    service: str  # the API path, "office/morning_prayer" or "readings/daily_office"
    office_name: str  # how an episode names the office: "Daily Morning Prayer"
    style: str = CONTEMPORARY
    evening: bool = False  # name the day by its evening commemoration
    proper_days_only: bool = False  # publish only days with proper Eucharistic readings
    keywords: tuple = field(default_factory=tuple)
    sort: int = 0

    @property
    def is_readings(self):
        return self.service.startswith("readings/")

    @property
    def settings(self):
        traditional = self.style == TRADITIONAL
        if self.is_readings:
            return dict(TRADITIONAL_READINGS_SETTINGS if traditional else READINGS_SETTINGS)
        return dict(TRADITIONAL_SETTINGS if traditional else CONTEMPORARY_SETTINGS)

    @property
    def readings_kind(self):
        return self.service.split("/", 1)[1] if self.is_readings else None

    @property
    def api_path(self):
        if self.is_readings:
            return f"/api/v1/readings_audio/{self.readings_kind}"
        return f"/api/v1/{self.service}"

    def api_query(self):
        """Query parameters for the audio request this feed's episodes are built from."""
        query = dict(self.settings)
        if self.is_readings:
            if self.proper_days_only:
                query["position"] = "principal"
        else:
            query["extra_collects"] = ""
        query["include_audio_links"] = "true"
        return query

    def follow_along_url(self, day):
        """The page that shows this episode's text, with the feed's own settings."""
        date_path = f"{day.year}/{day.month}/{day.day}"
        if self.is_readings:
            # The Readings page takes its translation, psalter, and (for the
            # Daily Office's psalms) psalm cycle from the link. The cycle is
            # ``cycle``, not ``psalter``, which the app applies as a site setting.
            query = {key: self.settings[key] for key in ("translation", "psalms")}
            if self.readings_kind == "daily_office":
                query["cycle"] = self.settings["psalter"]
            return f"{SITE_URL}/readings/{self.readings_kind}/{date_path}?{urlencode(query)}"
        group, office = self.service.split("/")
        path = f"family/{office}" if group == "family" else office
        return f"{SITE_URL}/{path}/{date_path}?{urlencode(self.settings)}"

    @property
    def style_label(self):
        if self.is_readings:
            if self.style == TRADITIONAL:
                return "King James Version (KJV), Coverdale Psalter"
            return "English Standard Version (ESV), Renewed Coverdale Psalter"
        if self.style == TRADITIONAL:
            return "Traditional prayer-book language, King James Version (KJV), Coverdale Psalter"
        return "Contemporary language, English Standard Version (ESV), Renewed Coverdale Psalter"


def _office(slug, title, subtitle, about, group, service, office_name, evening=False, sort=0, keywords=()):
    feeds = []
    for style in (CONTEMPORARY, TRADITIONAL):
        traditional = style == TRADITIONAL
        language = (
            "In traditional prayer-book language (thee and thou), with the King James Version and the Coverdale Psalter."
            if traditional
            else "In contemporary language, with the English Standard Version and the Renewed Coverdale Psalter."
        )
        feeds.append(
            PodcastFeed(
                slug=f"{slug}-traditional" if traditional else slug,
                title=f"{title} (Traditional Language)" if traditional else title,
                subtitle=subtitle + (" In traditional language." if traditional else ""),
                description=(
                    f"{about}\n\n{language} A new episode every day, each the complete office for that day, "
                    "with a link to pray along with the full text at dailyoffice2019.com.\n\n"
                    f"{SYNTHESIZED_VOICE_NOTE} The Daily Office follows the Book of Common Prayer (2019) of the "
                    "Anglican Church in North America."
                ),
                group=group,
                service=service,
                office_name=office_name,
                style=style,
                evening=evening,
                sort=sort * 2 + int(traditional),
                keywords=keywords + (("traditional language", "King James Version") if traditional else ("ESV",)),
            )
        )
    return feeds


def _readings(
    slug, title, subtitle, about, details, service, office_name, proper_days_only=False, sort=0, keywords=()
):
    """A readings podcast in the ESV and its traditional-language (KJV) twin.

    ``details`` names the translation with a ``{version}`` placeholder.
    """
    feeds = []
    for style in (CONTEMPORARY, TRADITIONAL):
        traditional = style == TRADITIONAL
        version = (
            "King James Version, with the Coverdale Psalter"
            if traditional
            else "English Standard Version, with the Renewed Coverdale Psalter"
        )
        feeds.append(
            PodcastFeed(
                slug=f"{slug}-traditional" if traditional else slug,
                title=f"{title} (Traditional Language)" if traditional else title,
                subtitle=subtitle + (" In the King James Version." if traditional else ""),
                description=f"{about}\n\n{details.format(version=version)}\n\n{SYNTHESIZED_VOICE_NOTE}",
                group="readings",
                service=service,
                office_name=office_name,
                style=style,
                proper_days_only=proper_days_only,
                sort=sort * 2 + int(traditional),
                keywords=keywords + (("King James Version", "KJV") if traditional else ("ESV",)),
            )
        )
    return feeds


COMMON_KEYWORDS = ("Book of Common Prayer", "Anglican", "daily prayer", "ACNA", "liturgy", "Scripture")

FEEDS = [
    *_office(
        "morning-prayer",
        "Morning Prayer",
        "Daily Morning Prayer from the Book of Common Prayer (2019), every day.",
        "Begin the day with the Church's ancient office of Morning Prayer. Each episode prays the whole "
        "office for the day: the opening sentence, the confession of sin, the Venite or Jubilate, the "
        "psalms appointed in the sixty-day psalter, lessons from the Old and New Testaments in the Daily "
        "Office lectionary, the canticles, the Apostles' Creed, the Lord's Prayer, the suffrages and "
        "collects, and the Great Litany on Wednesdays, Fridays, and Sundays.",
        "daily-office",
        "office/morning_prayer",
        "Daily Morning Prayer",
        sort=0,
        keywords=COMMON_KEYWORDS + ("Morning Prayer", "Matins", "Daily Office"),
    ),
    *_office(
        "midday-prayer",
        "Midday Prayer",
        "A short office of prayer at noon from the Book of Common Prayer (2019), every day.",
        "Pause in the middle of the day for the brief office of Midday Prayer: a psalm, a short reading "
        "of Scripture, the Lord's Prayer, and prayers and collects for the middle of the day. Short enough "
        "to pray at your desk, on a walk, or over lunch.",
        "daily-office",
        "office/midday_prayer",
        "Daily Midday Prayer",
        sort=1,
        keywords=COMMON_KEYWORDS + ("Midday Prayer", "Noonday Prayer", "Daily Office"),
    ),
    *_office(
        "evening-prayer",
        "Evening Prayer",
        "Daily Evening Prayer (Evensong) from the Book of Common Prayer (2019), every day.",
        "End the working day with Evening Prayer. Each episode prays the whole office for the day: the "
        "opening sentence, the confession of sin, the Phos Hilaron, the psalms appointed in the sixty-day "
        "psalter, the evening lessons from the Daily Office lectionary, the canticles, the Apostles' Creed, the Lord's Prayer, the suffrages and collects, and the dismissal.",
        "daily-office",
        "office/evening_prayer",
        "Daily Evening Prayer",
        evening=True,
        sort=2,
        keywords=COMMON_KEYWORDS + ("Evening Prayer", "Evensong", "Vespers", "Daily Office"),
    ),
    *_office(
        "compline",
        "Compline",
        "Prayer at the close of the day from the Book of Common Prayer (2019), every night.",
        "Close the day with Compline, the quiet office prayed before sleep: confession, the psalms of "
        "trust, a short reading, “Into your hands, O Lord, I commend my spirit,” the Song of "
        "Simeon, and prayers for protection through the night.",
        "daily-office",
        "office/compline",
        "Compline",
        evening=True,
        sort=3,
        keywords=COMMON_KEYWORDS + ("Compline", "night prayer", "bedtime prayer", "Daily Office"),
    ),
    *_office(
        "family-morning-prayer",
        "Family Prayer in the Morning",
        "Short morning devotions for households from the Book of Common Prayer (2019).",
        "Family Prayer is the Prayer Book's short form of daily prayer for households, families, and anyone "
        "with only a few minutes. In the morning: an opening sentence, a psalm, a brief reading from "
        "Scripture, the Apostles' Creed, the Lord's Prayer, and a collect for the morning. A few minutes "
        "to pray together over breakfast or on the way to school.",
        "family",
        "family/morning_prayer",
        "Family Prayer in the Morning",
        sort=4,
        keywords=COMMON_KEYWORDS + ("family prayer", "family devotions", "morning devotional", "kids"),
    ),
    *_office(
        "family-midday-prayer",
        "Family Prayer at Midday",
        "Short midday devotions for households from the Book of Common Prayer (2019).",
        "Family Prayer is the Prayer Book's short form of daily prayer for households, families, and anyone "
        "with only a few minutes. At midday: an opening sentence, a psalm, a brief reading from Scripture, "
        "the Lord's Prayer, and a collect for the middle of the day.",
        "family",
        "family/midday_prayer",
        "Family Prayer at Midday",
        sort=5,
        keywords=COMMON_KEYWORDS + ("family prayer", "family devotions", "midday prayer", "kids"),
    ),
    *_office(
        "family-early-evening-prayer",
        "Family Prayer in the Early Evening",
        "Short evening devotions for households from the Book of Common Prayer (2019).",
        "Family Prayer is the Prayer Book's short form of daily prayer for households, families, and anyone "
        "with only a few minutes. In the early evening: an opening sentence, the Phos Hilaron, a brief "
        "reading from Scripture, the Apostles' Creed, the Lord's Prayer, and a collect for the evening. A few "
        "minutes to pray together around the dinner table.",
        "family",
        "family/early_evening_prayer",
        "Family Prayer in the Early Evening",
        evening=True,
        sort=6,
        keywords=COMMON_KEYWORDS + ("family prayer", "family devotions", "evening devotional", "kids"),
    ),
    *_office(
        "family-close-of-day-prayer",
        "Family Prayer at the Close of Day",
        "Short bedtime devotions for households from the Book of Common Prayer (2019).",
        "Family Prayer is the Prayer Book's short form of daily prayer for households, families, and anyone "
        "with only a few minutes. At the close of day: an opening sentence, a psalm, a brief reading from "
        "Scripture, the Apostles' Creed, prayers for the night, the Lord's Prayer, and the Song of Simeon. "
        "A few minutes to pray together at bedtime.",
        "family",
        "family/close_of_day_prayer",
        "Family Prayer at the Close of Day",
        evening=True,
        sort=7,
        keywords=COMMON_KEYWORDS + ("family prayer", "bedtime prayer", "night prayer", "kids"),
    ),
    *_readings(
        "daily-office-readings",
        "Daily Office Readings",
        "The psalms and lessons appointed for Morning and Evening Prayer, every day.",
        "Hear the whole of Scripture over the year. Each episode reads the psalms and lessons appointed "
        "for the day in the Daily Office lectionary of the Book of Common Prayer (2019): Morning Prayer's "
        "psalms and Old and New Testament lessons, then Evening Prayer's. Just the readings, with no "
        "other prayers, for the commute, the gym, or alongside your own prayers.",
        "{version} in the sixty-day cycle. A new episode every day, with a link to the day's readings at "
        "dailyoffice2019.com.",
        "readings/daily_office",
        "Readings for the Daily Office",
        sort=8,
        keywords=COMMON_KEYWORDS + ("Bible reading", "lectionary", "Daily Office", "Bible in a year"),
    ),
    *_readings(
        "holy-eucharist-readings",
        "Holy Eucharist Readings",
        "The collect and lessons for every Sunday and holy day, before you hear them in church.",
        "Prepare for Sunday. Each episode reads the Collect of the Day, the Old Testament lesson, the "
        "psalm, the Epistle, and the Holy Gospel appointed for the Holy Eucharist in the Book of Common "
        "Prayer (2019) lectionary. Episodes appear only for days with their own readings: every Sunday, "
        "the principal feasts, the holy days of the apostles and evangelists, and the days of Holy Week "
        "and Easter Week.",
        "{version}. Each episode links to the day's readings at dailyoffice2019.com.",
        "readings/holy_eucharist",
        "Readings for the Holy Eucharist",
        proper_days_only=True,
        sort=9,
        keywords=COMMON_KEYWORDS + ("Sunday readings", "lectionary", "Eucharist", "Gospel", "sermon prep"),
    ),
]

FEEDS = sorted(FEEDS, key=lambda feed: feed.sort)
FEEDS_BY_SLUG = {feed.slug: feed for feed in FEEDS}

GROUPS = [
    {
        "slug": "daily-office",
        "title": "The Daily Office",
        "description": "The four offices of the day, prayed in full.",
    },
    {
        "slug": "family",
        "title": "Family Prayer",
        "description": "Short devotions for households, a few minutes each.",
    },
    {
        "slug": "readings",
        "title": "Just the Readings",
        "description": "The appointed Scripture, read without the rest of the office.",
    },
]

# The listener-recorded alternative, offered on the landing page.
LIVE_ALTERNATIVE = {
    "title": "The Daily Office Podcast",
    "host": "Andrew Russell",
    "description": (
        "Andrew Russell records Morning and Evening Prayer from the 2019 Book of Common Prayer every day, "
        "with the one-year Daily Office lectionary and the sixty-day psalter."
    ),
    "links": [
        {"platform": "apple", "url": "https://podcasts.apple.com/us/podcast/the-daily-office-podcast/id1574821838"},
        {"platform": "spotify", "url": "https://dailyofficepodcast.captivate.fm/spotify"},
        {"platform": "overcast", "url": "https://overcast.fm/itunes1574821838"},
        {"platform": "castro", "url": "https://castro.fm/itunes/1574821838"},
        {"platform": "goodpods", "url": "https://www.goodpods.com/podcasts-aid/1574821838"},
        {"platform": "website", "url": "https://dailyofficepodcast.captivate.fm"},
        {"platform": "rss", "url": "https://dailyofficepodcast.captivate.fm/rssfeed"},
    ],
}


def get_feed(slug):
    try:
        return FEEDS_BY_SLUG[slug]
    except KeyError:
        raise KeyError(f"Unknown podcast feed: {slug}") from None
