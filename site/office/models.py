import datetime
import re
from functools import cached_property

from bs4 import BeautifulSoup
from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

from churchcal.base_models import BaseModel
from churchcal.models import Commemoration, Proper, Common, SanctoraleCommemoration
from office.utils import passage_to_citation


class OfficeDay(BaseModel):
    TESTAMENTS = (("OT", "Old Testament"), ("DC", "Deuterocanon"), ("AP", "Apocrypha"), ("NT", "New Testament"))

    holy_day_name = models.CharField(max_length=255, null=True, blank=True)
    mp_psalms = models.CharField(max_length=255)
    mp_reading_1 = models.CharField(max_length=255)
    mp_reading_1_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    mp_reading_1_text = models.TextField(blank=True, null=True)
    mp_reading_1_abbreviated = models.CharField(max_length=255, null=True, blank=True)
    mp_reading_1_abbreviated_text = models.TextField(blank=True, null=True)
    mp_reading_2 = models.CharField(max_length=255)
    mp_reading_2_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    mp_reading_2_text = models.TextField(blank=True, null=True)
    ep_psalms = models.CharField(max_length=255)
    ep_reading_1 = models.CharField(max_length=255)
    ep_reading_1_text = models.TextField(blank=True, null=True)
    ep_reading_1_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    ep_reading_1_abbreviated = models.CharField(max_length=255, null=True, blank=True)
    ep_reading_1_abbreviated_text = models.TextField(blank=True, null=True)
    ep_reading_2 = models.CharField(max_length=255)
    ep_reading_2_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    ep_reading_2_text = models.TextField(blank=True, null=True)

    @cached_property
    def readings(self):
        passages = Scripture.objects.filter(
            passage__in=[
                self.mp_reading_1,
                self.mp_reading_1_abbreviated,
                self.mp_reading_2,
                self.ep_reading_1,
                self.ep_reading_1_abbreviated,
                self.ep_reading_2,
            ]
        ).all()
        return {passage.passage: passage for passage in passages if passage}

    # Fallback translations for versions that don't include deuterocanonical books
    TRANSLATION_FALLBACKS = {
        "cuvs": "znsigao",
        "cuv": "sigao",
        "esv": "nrsvce",
        "niv": "nrsvce",
        "nasb": "nrsvce",
        "sigao": "nrsvce",
        "znsigao": "nrsvce",
        "nvi": "nrsvce",
        "rv1960": "nvi",
    }

    def passage_to_text(self, attribute, translation="esv"):
        translation = Scripture.normalize_bible_translation(translation)
        passage = getattr(self, attribute)
        if not passage and "_abbreviated" in attribute:
            attribute = attribute.replace("_abbreviated", "")
            passage = getattr(self, attribute)
        try:
            result = getattr(self.readings[passage], translation)
            if not result or result.strip() in ["", "-"]:
                fallback = self.TRANSLATION_FALLBACKS.get(translation, "nrsvce")
                result = getattr(self.readings[passage], fallback, None)
            if not result or result.strip() in ["", "-"]:
                result = self.readings[passage].nrsvce
            return result
        except (KeyError, AttributeError):
            return None

    def __getattribute__(self, attrname):
        value = super().__getattribute__(attrname)
        try:
            return value.replace("<h3>", "<h3 class='reading-heading off'>")
        except (AttributeError, TypeError):
            return value


class StandardOfficeDay(OfficeDay):
    month = models.IntegerField()
    day = models.IntegerField()


class HolyDayOfficeDay(OfficeDay):
    commemoration = models.ForeignKey(Commemoration, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)


class ThirtyDayPsalterDay(BaseModel):
    day = models.IntegerField()
    mp_psalms = models.CharField(max_length=255)
    ep_psalms = models.CharField(max_length=255)

    def psalm_string_to_list(self, psalms):
        return psalms.split(psalms)

    def get_mp_pslams(self):
        return self.psalm_string_to_list(self.mp_psalms)

    def get_ep_pslams(self):
        return self.psalm_string_to_list(self.ep_psalms)


class AboutItem(BaseModel):
    question = models.CharField(max_length=4000)
    answer = CKEditor5Field()
    app_mode = models.BooleanField(default=True)
    web_mode = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    @property
    def question_for_web(self):
        if self.mode == "app":
            return None
        return self.question.replace("{medium}", "site")

    @property
    def answer_for_web(self):
        if self.mode == "app":
            return None
        return self.answer.replace("{medium}", "site")

    @property
    def question_for_app(self):
        if self.mode == "web":
            return None
        return self.question.replace("{medium}", "app")

    @property
    def answer_for_app(self):
        if self.mode == "web":
            return None
        return self.answer.replace("{medium}", "app")

    def mode(self):
        if self.web_mode and self.app_mode:
            return "both"
        if self.web_mode:
            return "web"
        return "app"

    def display_name(self):
        return "{} ({})".format(re.sub(r"<[^<]+?>", "", self.question), self.mode())

    def __str__(self):
        return self.display_name()

    class Meta(object):
        ordering = ["order"]


class UpdateNotice(BaseModel):
    notice = CKEditor5Field()
    app_mode = models.BooleanField(default=True)
    web_mode = models.BooleanField(default=True)
    version = models.FloatField()

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    def mode(self):
        if self.web_mode and self.app_mode:
            return "both"
        if self.web_mode:
            return "web"
        return "app"

    class Meta(object):
        ordering = ["-version"]


class Setting(BaseModel):
    MAIN_SETTINGS = 1
    ADDITIONAL_SETTINGS = 2
    EXPERT_SETTINGS = 3
    SETTING_TYPES = (
        (MAIN_SETTINGS, "Settings"),
        (ADDITIONAL_SETTINGS, "Additional Settings"),
        (EXPERT_SETTINGS, "Expert Settings"),
    )

    DAILY_OFFICE_SITE = 1
    FAMILY_PRAYER_SITE = 2
    SETTING_SITES = (
        (DAILY_OFFICE_SITE, "Daily Office"),
        (FAMILY_PRAYER_SITE, "Family Prayer"),
    )

    name = models.CharField(max_length=255)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    setting_type = models.PositiveSmallIntegerField(choices=SETTING_TYPES, null=False, default=MAIN_SETTINGS)
    site = models.PositiveSmallIntegerField(choices=SETTING_SITES, null=False, default=DAILY_OFFICE_SITE)
    setting_string_order = models.PositiveSmallIntegerField(null=False, default=0)


class SettingOption(BaseModel):
    DEFAULT_ABBREVIATION = "A"
    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    value = models.CharField(max_length=255)
    abbreviation = models.CharField(null=False, max_length=1, default=DEFAULT_ABBREVIATION)


class AudioGenerationConfig(BaseModel):
    class ProviderMode(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        ELEVENLABS_V3 = "elevenlabs_v3", "ElevenLabs v3"
        ELEVENLABS_STUDIO = "elevenlabs_studio", "ElevenLabs Studio"

    class TextNormalization(models.TextChoices):
        AUTO = "auto", "Auto"
        ON = "on", "On"
        OFF = "off", "Off"

    name = models.CharField(max_length=255, unique=True, default="default")
    provider_mode = models.CharField(max_length=32, choices=ProviderMode.choices, default=ProviderMode.OPENAI)
    openai_model = models.CharField(max_length=64, default="tts-1")
    openai_output_format = models.CharField(max_length=32, default="mp3")
    elevenlabs_model_id = models.CharField(max_length=64, default="eleven_v3")
    elevenlabs_sound_model_id = models.CharField(max_length=64, default="eleven_v3")
    elevenlabs_output_format = models.CharField(max_length=64, default="mp3_44100_128")
    elevenlabs_language_code = models.CharField(max_length=16, null=True, blank=True)
    elevenlabs_apply_text_normalization = models.CharField(
        max_length=16,
        choices=TextNormalization.choices,
        default=TextNormalization.AUTO,
    )
    elevenlabs_seed = models.PositiveBigIntegerField(null=True, blank=True)
    elevenlabs_studio_enabled = models.BooleanField(default=False)
    elevenlabs_studio_access_granted = models.BooleanField(default=False)
    elevenlabs_studio_last_checked = models.DateTimeField(null=True, blank=True)
    elevenlabs_studio_last_error = models.TextField(null=True, blank=True)
    sound_default_duration_seconds = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sound_prompt_influence = models.DecimalField(max_digits=4, decimal_places=3, default=0.300)
    sound_loop = models.BooleanField(default=False)
    spoken_chunk_target_characters = models.PositiveSmallIntegerField(default=1800)
    spoken_chunk_max_characters = models.PositiveSmallIntegerField(default=2000)
    assembly_target_loudness_lufs = models.DecimalField(max_digits=5, decimal_places=2, default=-18.00)
    sound_target_loudness_lufs = models.DecimalField(max_digits=5, decimal_places=2, default=-22.00)
    module_boundary_padding_ms = models.PositiveSmallIntegerField(default=120)
    settings_notes = models.TextField(null=True, blank=True)

    @classmethod
    def get_solo(cls):
        config, _ = cls.objects.get_or_create(name="default")
        return config

    def save(self, *args, **kwargs):
        if self.elevenlabs_model_id != "eleven_v3":
            self.elevenlabs_model_id = "eleven_v3"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Audio generation ({self.get_provider_mode_display()})"


class AudioVoice(BaseModel):
    class Provider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        ELEVENLABS = "elevenlabs", "ElevenLabs"

    class Role(models.TextChoices):
        LEADER = "leader", "Leader"
        LEADER_DIALOGUE = "leader_dialogue", "Leader Dialogue"
        CONGREGATION = "congregation", "Congregation"
        CONGREGATION_DIALOGUE = "congregation_dialogue", "Congregation Dialogue"
        READER = "reader", "Reader"

    provider = models.CharField(max_length=32, choices=Provider.choices)
    role = models.CharField(max_length=32, choices=Role.choices)
    name = models.CharField(max_length=255)
    voice_id = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("provider", "role", "order", "name")
        indexes = [
            models.Index(fields=["provider", "role", "enabled"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider}, {self.role})"


class AudioGeneratedFile(BaseModel):
    class Provider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        ELEVENLABS = "elevenlabs", "ElevenLabs"
        LOCAL = "local", "Local"

    class GenerationType(models.TextChoices):
        SPOKEN = "spoken", "Spoken"
        SOUND = "sound", "Sound"
        SILENCE = "silence", "Silence"
        MODULE = "module", "Module"
        FINAL = "final", "Final"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"
        DISABLED = "disabled", "Disabled"
        DELETED = "deleted", "Deleted"
        MISSING = "missing", "Missing"

    provider = models.CharField(max_length=32, choices=Provider.choices)
    provider_mode = models.CharField(max_length=32, default=AudioGenerationConfig.ProviderMode.OPENAI)
    generation_type = models.CharField(max_length=32, choices=GenerationType.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    cache_key = models.CharField(max_length=128, db_index=True)
    content_hash = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    text_preview = models.TextField(null=True, blank=True)
    voice_key = models.CharField(max_length=512, null=True, blank=True)
    voices = models.JSONField(default=dict, blank=True)
    model_id = models.CharField(max_length=128, null=True, blank=True)
    endpoint = models.CharField(max_length=255, null=True, blank=True)
    settings_hash = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    settings_snapshot = models.JSONField(default=dict, blank=True)
    office = models.CharField(max_length=128, null=True, blank=True)
    office_date = models.DateField(null=True, blank=True)
    module_name = models.CharField(max_length=255, null=True, blank=True)
    line_type = models.CharField(max_length=64, null=True, blank=True)
    line_id = models.CharField(max_length=255, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    media_path = models.CharField(max_length=512, null=True, blank=True)
    duration_seconds = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    characters = models.PositiveIntegerField(default=0)
    cost_units = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    cost_source = models.CharField(max_length=64, default="unpriced")
    request_id = models.CharField(max_length=255, null=True, blank=True)
    response_metadata = models.JSONField(default=dict, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=["provider", "provider_mode", "generation_type"]),
            models.Index(fields=["status", "disabled_at", "deleted_at"]),
            models.Index(fields=["office_date", "module_name"]),
        ]

    @property
    def is_reusable(self):
        return self.status == self.Status.READY and self.disabled_at is None and self.deleted_at is None

    def mark_disabled(self):
        self.disabled_at = timezone.now()
        self.status = self.Status.DISABLED
        self.save(update_fields=["disabled_at", "status", "updated"])

    def mark_deleted(self):
        self.deleted_at = timezone.now()
        self.status = self.Status.DELETED
        self.save(update_fields=["deleted_at", "status", "updated"])

    def __str__(self):
        return f"{self.generation_type} {self.provider_mode} {self.cache_key[:12]}"


class AudioGenerationEvent(BaseModel):
    class Action(models.TextChoices):
        GENERATED = "generated", "Generated"
        CACHE_HIT = "cache_hit", "Cache hit"
        CACHE_SKIP = "cache_skip", "Cache skip"
        ASSEMBLED = "assembled", "Assembled"
        FALLBACK = "fallback", "Fallback"
        HEALTH_CHECK = "health_check", "Health check"
        ERROR = "error", "Error"

    generated_file = models.ForeignKey(
        AudioGeneratedFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    provider = models.CharField(max_length=32, null=True, blank=True)
    provider_mode = models.CharField(max_length=32, null=True, blank=True)
    generation_type = models.CharField(max_length=32, null=True, blank=True)
    model_id = models.CharField(max_length=128, null=True, blank=True)
    cache_key = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    office = models.CharField(max_length=128, null=True, blank=True)
    office_date = models.DateField(null=True, blank=True)
    module_name = models.CharField(max_length=255, null=True, blank=True)
    settings_hash = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    characters = models.PositiveIntegerField(default=0)
    cost_units = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    request_id = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=["provider", "provider_mode", "generation_type"]),
            models.Index(fields=["office_date", "module_name"]),
            models.Index(fields=["action", "created"]),
        ]

    def __str__(self):
        return f"{self.action} {self.provider_mode or ''} {self.generation_type or ''}".strip()


class AudioUsage(BaseModel):
    generated_file = models.ForeignKey(AudioGeneratedFile, on_delete=models.CASCADE, related_name="usage_links")
    office = models.CharField(max_length=128, null=True, blank=True)
    office_date = models.DateField(null=True, blank=True)
    module_name = models.CharField(max_length=255, null=True, blank=True)
    line_id = models.CharField(max_length=255, null=True, blank=True)
    line_type = models.CharField(max_length=64, null=True, blank=True)
    provider_mode = models.CharField(max_length=32, null=True, blank=True)
    generation_type = models.CharField(max_length=32, null=True, blank=True)
    settings_hash = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    settings_snapshot = models.JSONField(default=dict, blank=True)
    start_time_seconds = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    duration_seconds = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    request_path = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=["office_date", "module_name"]),
            models.Index(fields=["provider_mode", "generation_type"]),
        ]

    def __str__(self):
        return f"{self.generated_file} used by {self.module_name or self.office or 'unknown'}"


class AudioCostRate(BaseModel):
    class Unit(models.TextChoices):
        CHARACTER = "character", "Character"
        COST_UNIT = "cost_unit", "Provider cost unit"
        MINUTE = "minute", "Audio minute"
        FILE = "file", "File"

    provider = models.CharField(max_length=32)
    model_id = models.CharField(max_length=128)
    generation_type = models.CharField(max_length=32, default=AudioGeneratedFile.GenerationType.SPOKEN)
    unit = models.CharField(max_length=32, choices=Unit.choices, default=Unit.CHARACTER)
    usd_per_unit = models.DecimalField(max_digits=12, decimal_places=8, default=0)
    effective_at = models.DateTimeField(default=timezone.now)
    enabled = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("-effective_at", "provider", "model_id")
        indexes = [
            models.Index(fields=["provider", "model_id", "generation_type", "enabled", "effective_at"]),
        ]

    def __str__(self):
        return f"{self.provider} {self.model_id} {self.generation_type}: {self.usd_per_unit}/{self.unit}"


class CollectType(BaseModel):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class CollectTagCategory(BaseModel):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class CollectTag(BaseModel):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    collect_tag_category = models.ForeignKey(CollectTagCategory, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class AbstractCollect(object):
    text = ""
    traditional_text = ""

    def __init__(self, text, traditional_text):
        self.text = text
        self.traditional_text = traditional_text

    @property
    def traditional_text_no_tags(self):
        from office.management.commands.import_collects import do_strip_tags

        return do_strip_tags(self.traditional_text).replace(" Amen.", "")

    @property
    def text_no_tags(self):
        from office.management.commands.import_collects import do_strip_tags

        return do_strip_tags(self.text).replace(" Amen.", "")


class Collect(BaseModel):
    COLLECT_TYPES = (
        ("year", "Collects of the Christian Year"),
        ("occasional", "Occasional Prayers"),
        ("office_prayers", "Collects from the Daily Office"),
        ("burial_rite", "Collects from the Burial Rite"),
        ("other", "Other Collects"),
    )

    title = models.CharField(max_length=255)
    text = CKEditor5Field()
    normalized_text = models.TextField(blank=True, null=True)
    traditional_text = CKEditor5Field(blank=True, null=True)
    normalized_traditional_text = models.TextField(blank=True, null=True)
    chinese_text = models.TextField(blank=True, null=True)
    spanish_text = models.TextField(blank=True, null=True)
    collect_type = models.ForeignKey(CollectType, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    number = models.PositiveSmallIntegerField(null=True, blank=True)
    tags = models.ManyToManyField(CollectTag)
    attribution = models.CharField(max_length=255, blank=True, null=True)
    metrical_collect = models.ForeignKey("office.MetricalCollect", null=True, blank=True, on_delete=models.SET_NULL)
    metrical_collect_2 = models.ForeignKey(
        "office.MetricalCollect", null=True, blank=True, on_delete=models.SET_NULL, related_name="metrical_collect_2"
    )
    metrical_collect_3 = models.ForeignKey(
        "office.MetricalCollect", null=True, blank=True, on_delete=models.SET_NULL, related_name="metrical_collect_3"
    )

    @property
    def traditional_text_no_tags(self):
        from office.management.commands.import_collects import do_strip_tags

        return do_strip_tags(self.traditional_text).replace(" Amen.", "")

    @property
    def text_no_tags(self):
        from office.management.commands.import_collects import do_strip_tags

        return do_strip_tags(self.text).replace(" Amen.", "")

    @property
    def chinese_text_no_tags(self):
        if not self.chinese_text:
            return None
        from office.management.commands.import_collects import do_strip_tags

        return do_strip_tags(self.chinese_text).replace("阿們。", "").replace(" Amen.", "").strip()

    @property
    def spanish_text_no_tags(self):
        if not self.spanish_text:
            return None
        from office.management.commands.import_collects import do_strip_tags

        return do_strip_tags(self.spanish_text).replace("Amén.", "").replace(" Amen.", "").strip()

    def __str__(self):
        return self.title


class Scripture(BaseModel):
    BIBLE_TRANSLATIONS = frozenset(
        {
            "esv",
            "kjv",
            "rsv",
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
        }
    )
    INVALID_TRANSLATION_VALUES = frozenset({"undefined", "null", "none"})

    @classmethod
    def normalize_bible_translation(cls, translation, default="esv"):
        if not translation:
            return default
        translation = str(translation).lower().strip()
        if translation in cls.INVALID_TRANSLATION_VALUES:
            return default
        if translation not in cls.BIBLE_TRANSLATIONS:
            return default
        return translation

    passage = models.CharField(max_length=255)
    esv = models.TextField(blank=True, null=True)
    kjv = models.TextField(blank=True, null=True)
    rsv = models.TextField(blank=True, null=True)
    nrsvce = models.TextField(blank=True, null=True)
    nabre = models.TextField(blank=True, null=True)
    niv = models.TextField(blank=True, null=True)
    nasb = models.TextField(blank=True, null=True)
    coverdale = models.TextField(blank=True, null=True)
    renewed_coverdale = models.TextField(blank=True, null=True)
    cuvs = models.TextField(blank=True, null=True)
    cuv = models.TextField(blank=True, null=True)
    sigao = models.TextField(blank=True, null=True)
    znsigao = models.TextField(blank=True, null=True)
    nvi = models.TextField(blank=True, null=True)
    rv1960 = models.TextField(blank=True, null=True)

    @staticmethod
    def no_headings(markup):
        if not markup:
            markup = ""
        soup = BeautifulSoup(markup, "html.parser")
        for sup in soup.find_all("h1"):
            sup.decompose()
        for sup in soup.find_all("h2"):
            sup.decompose()
        for div in soup.find_all("h3"):
            div.decompose()
        for div in soup.find_all("h4"):
            div.decompose()
        for div in soup.find_all("h5"):
            div.decompose()

        return str(soup)

    @property
    def esv_no_headings(self):
        return self.no_headings(self.esv)

    @property
    def kjv_no_headings(self):
        return self.no_headings(self.kjv)

    @property
    def rsv_no_headings(self):
        return self.no_headings(self.rsv)

    @property
    def nrsvce_no_headings(self):
        return self.no_headings(self.nrsvce)

    @property
    def nabre_no_headings(self):
        return self.no_headings(self.nabre)

    @property
    def niv_no_headings(self):
        return self.no_headings(self.niv)

    @property
    def nasb_no_headings(self):
        return self.no_headings(self.nasb)

    @property
    def coverdale_no_headings(self):
        return self.no_headings(self.coverdale)

    @property
    def renewed_coverdale_no_headings(self):
        return self.no_headings(self.renewed_coverdale)

    @property
    def nvi_no_headings(self):
        return self.no_headings(self.nvi)

    @property
    def rv1960_no_headings(self):
        return self.no_headings(self.rv1960)

    @property
    def apocrypha(self):
        return self.esv == "-" or self.esv == ""

    @property
    def ending_call(self):
        if "Psalm" in self.passage:
            return ""
        first_word = self.passage.split(" ")[0]
        if first_word in ["Matthew", "Mark", "Luke", "John"]:
            return "The Gospel of the Lord."
        return "Here ends the reading" if self.apocrypha else "The Word of the Lord"

    @property
    def ending_response(self):
        if "Psalm" in self.passage:
            return ""
        first_word = self.passage.split(" ")[0]
        if first_word in ["Matthew", "Mark", "Luke", "John"]:
            return "Praise to you, Lord Christ."
        return "" if self.apocrypha else "Thanks be to God"

    @property
    def citation(self):
        try:
            if "Psalm" in self.passage:
                return ""
            return passage_to_citation(self.passage, mass=True)
        except Exception as e:
            print(e)
            return "Error"

    @property
    def initial_response(self):
        try:
            first_word = self.passage.split(" ")[0]
            if first_word in ["Matthew", "Mark", "Luke", "John"]:
                return "Glory to you, Lord Christ."
            return ""
        except Exception as e:
            return ""


class LectionaryItem(BaseModel):
    commemoration = models.ForeignKey(Commemoration, on_delete=models.SET_NULL, null=True, blank=True)
    sanctorale_commemoration = models.ForeignKey(
        SanctoraleCommemoration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sanctorale_lectionary_items",
    )
    proper = models.ForeignKey(Proper, on_delete=models.SET_NULL, null=True, blank=True)
    common = models.ForeignKey(Common, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    service = models.CharField(max_length=255)

    @cached_property
    def name(self):
        if self.commemoration:
            return self.commemoration.name
        if self.proper:
            return f"Proper {self.proper.number}"
        if self.common:
            return self.common.name
        return "Lectionary Entry"

    @cached_property
    def name_and_service(self):
        if self.service:
            return f"{self.name} ({self.service})"
        return self.name

    @cached_property
    def mass_readings(self):
        if self.commemoration:
            mass_readings = self.commemoration.mass_readings
            return [mass_reading for mass_reading in mass_readings if mass_reading.service == self.service]
        if self.proper:
            return self.proper.mass_readings
        if self.common:
            return self.common.mass_readings

    def mass_readings_by_year(self, year="A"):
        return [reading for reading in self.mass_readings if year in reading.years]

    @cached_property
    def year_a(self):
        return self.mass_readings_by_year("A")

    @cached_property
    def year_b(self):
        return self.mass_readings_by_year("B")

    @cached_property
    def year_c(self):
        return self.mass_readings_by_year("C")

    @cached_property
    def date_string(self):
        if self.sanctorale_commemoration:
            date_string = datetime.datetime(
                2019, self.sanctorale_commemoration.month, self.sanctorale_commemoration.day
            )
            return date_string.strftime("%B %-d")
        if self.proper:
            start = self.proper.start_date.strftime("%B %-d")
            end = self.proper.end_date.strftime("%B %-d")
            if self.proper.number in [1, 2]:
                return f"Weekdays following the Sunday from {start} to {end}"
            return f"Sunday from {start} to {end}"
        return ""

    def year_to_readings(self, year):
        if year.upper() == "B":
            return self.year_b
        elif year.upper() == "C":
            return self.year_c
        else:
            return self.year_a

    def combine_short_and_long_passage(self, reading, year):
        year = year.upper().strip()
        if not reading.short_scripture:
            return f'<a href="/mass_readings/{year}/#{self.pk}_{reading.long_scripture.pk}">{reading.long_scripture.passage}</a>'
        short_passage = re.sub(r"[a-zA-Z]", "", reading.short_scripture.passage).strip()
        return f'<a href="/mass_readings/{year}/#{self.pk}_{reading.long_scripture.pk}">{reading.long_scripture.passage} [<em> or, {short_passage}</em> ]</a>'

    def passages_for_year_and_number(self, year, number):
        readings = self.year_to_readings(year)
        readings = [
            self.combine_short_and_long_passage(reading, year)
            for reading in readings
            if reading.reading_number == number
        ]
        return " <em>or</em> ".join(readings)

    def reading_1_passages(self, year):
        return self.passages_for_year_and_number(year, 1)

    def reading_2_passages(self, year):
        return self.passages_for_year_and_number(year, 2)

    def reading_3_passages(self, year):
        return self.passages_for_year_and_number(year, 3)

    def reading_4_passages(self, year):
        return self.passages_for_year_and_number(year, 4)

    @cached_property
    def reading_1_a_passages(self):
        return self.reading_1_passages(year="A")

    @cached_property
    def reading_2_a_passages(self):
        return self.reading_2_passages(year="A")

    @cached_property
    def reading_3_a_passages(self):
        return self.reading_3_passages(year="A")

    @cached_property
    def reading_4_a_passages(self):
        return self.reading_4_passages(year="A")

    @cached_property
    def reading_1_b_passages(self):
        return self.reading_1_passages(year="B")

    @cached_property
    def reading_2_b_passages(self):
        return self.reading_2_passages(year="B")

    @cached_property
    def reading_3_b_passages(self):
        return self.reading_3_passages(year="B")

    @cached_property
    def reading_4_b_passages(self):
        return self.reading_4_passages(year="B")

    @cached_property
    def reading_1_c_passages(self):
        return self.reading_1_passages(year="C")

    @cached_property
    def reading_2_c_passages(self):
        return self.reading_2_passages(year="C")

    @cached_property
    def reading_3_c_passages(self):
        return self.reading_3_passages(year="C")

    @cached_property
    def reading_4_c_passages(self):
        return self.reading_4_passages(year="C")

    @cached_property
    def collects(self):
        collects = []
        if self.commemoration:
            if self.commemoration.collect_1:
                collects.append(self.commemoration.collect_1)
            if self.commemoration.collect_2:
                collects.append(self.commemoration.collect_2)
            if self.commemoration.collect_eve:
                collects.append(self.commemoration.collect_eve)
        if self.proper:
            if self.proper.collect_1:
                collects.append(self.proper.collect_1)
        if self.common:
            if self.common.collect_1:
                collects.append(self.common.collect_1)
            if self.common.collect_2:
                collects.append(self.common.collect_2)
        return collects


class MetricalCollect(BaseModel):
    collect_number = models.PositiveSmallIntegerField(null=True, blank=True)
    original_collect = models.TextField(max_length=255, null=True, blank=True)
    normalized_original_collect = models.TextField(max_length=255, null=True, blank=True)
    tune_name = models.CharField(max_length=255, null=True, blank=True)
    first_line = models.CharField(max_length=255, null=True, blank=True)
    pdf_link = models.URLField(null=True, blank=True)
    site_link = models.URLField(null=True, blank=True)
    midi_link = models.URLField(null=True, blank=True)
    lyrics = models.TextField(null=True, blank=True)
    text_source = models.CharField(max_length=255, null=True, blank=True)
    tune_source = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
