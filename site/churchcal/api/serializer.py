import re

from rest_framework import serializers


class RankSerializer(serializers.Serializer):
    name = serializers.CharField()
    formatted_name = serializers.CharField()
    precedence = serializers.IntegerField(source="precedence_rank")


class CommemorationSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    name = serializers.CharField()
    rank = RankSerializer()
    colors = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()
    # collects = serializers.SerializerMethodField()
    collect = serializers.SerializerMethodField()
    biography = serializers.CharField()
    image_link = serializers.URLField()

    ai_bullet_points = serializers.SerializerMethodField()
    ai_bullet_points_citations = serializers.ListField(child=serializers.CharField())
    ai_foods = serializers.SerializerMethodField()
    ai_foods_citations = serializers.ListField(child=serializers.CharField())
    ai_hagiography = serializers.CharField()
    ai_hagiography_citations = serializers.ListField(child=serializers.CharField())
    ai_legend = serializers.CharField()
    ai_legend_citations = serializers.ListField(child=serializers.CharField())
    ai_lesser_feasts_and_fasts = serializers.CharField()
    ai_martyrology = serializers.CharField()
    ai_one_sentence = serializers.SerializerMethodField()
    ai_quote = serializers.CharField()
    ai_quote_by = serializers.CharField()
    ai_quote_citations = serializers.ListField(child=serializers.CharField())
    ai_traditions = serializers.SerializerMethodField()
    ai_traditions_citations = serializers.ListField(child=serializers.CharField())
    ai_verse = serializers.CharField()
    ai_verse_citation = serializers.CharField()

    # def combine_with_citations(self, text, citations):
    #
    #     def replace_match(match):
    #         index = int(match.group(1)) + 1
    #         # Extract the integer inside brackets
    #         value = f'<a href="{citations[index]}"><i class="fa-duotone fa-arrow-up-right-from-square"></i></a>'
    #         return value if 0 <= index < len(citations) else match.group(
    #             0)  # Replace if valid, else keep original
    #
    #     return re.sub(r'\[(\d+)\]', replace_match, text)

    def remove_citations(self, text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\[\d+\]", "", text)

    def parse_bullets(self, text):
        if text:
            text = text.strip()
            if text[0] == "-":
                pattern = r"\s[-]\s"
            elif text[0] == "•":
                pattern = r"\s[•]\s"
            else:
                pattern = r"\s[-•]\s"
            items = re.split(pattern, text)
            items = [re.sub(r"^[\s\-\•]+", "", item) for item in items]
            if items:
                return items
            return [text]
        return ""

    def get_ai_one_sentence(self, obj):
        return self.remove_citations(obj.ai_one_sentence)

    def get_ai_bullet_points(self, obj):
        return self.parse_bullets(obj.ai_bullet_points)

    def get_ai_foods(self, obj):
        return self.parse_bullets(obj.ai_foods)

    def get_ai_traditions(self, obj):
        return self.parse_bullets(obj.ai_traditions)

    def get_colors(self, obj):
        colors = [obj.color, obj.additional_color, obj.alternate_color, obj.alternate_color_2]
        return [color.lower() for color in colors if color]

    def get_links(self, obj):
        links = [obj.link_1, obj.link_2, obj.link_3]
        return [link for link in links if link]

    def get_collect(self, obj):
        if hasattr(obj, "morning_prayer_collect"):
            return obj.morning_prayer_collect.text

    def get_collects(self, obj):
        return {
            "collect": obj.morning_prayer_collect.text,
            "alternate_collect": (
                obj.evening_prayer_collect.text if obj.evening_prayer_collect != obj.morning_prayer_collect else None
            ),
            "vigil_collect": None if not obj.collect_eve else obj.collect_eve.text,
        }


class SeasonSerializer(serializers.Serializer):
    name = serializers.CharField()
    colors = serializers.SerializerMethodField()

    def get_colors(self, obj):
        colors = [obj.color, obj.alternate_color]
        return [color.lower() for color in colors if color]


class DaySerializer(serializers.Serializer):
    date = serializers.DateField()
    date_description = serializers.SerializerMethodField()
    season = SeasonSerializer()
    fast = serializers.SerializerMethodField()
    commemorations = CommemorationSerializer(many=True, source="all")
    evening_commemorations = CommemorationSerializer(many=True, source="all_evening")
    mass_readings = serializers.SerializerMethodField()
    primary_color = serializers.SerializerMethodField()
    primary_evening_color = serializers.SerializerMethodField()
    primary_feast = serializers.SerializerMethodField()
    primary_evening_feast = serializers.SerializerMethodField()
    major_feast = serializers.SerializerMethodField()
    major_or_minor_feast = serializers.SerializerMethodField()

    def get_date_description(self, obj):
        return {
            "date": obj.date.strftime("%Y-%-m-%-d"),
            "weekday": obj.date.strftime("%A"),
            "month": obj.date.strftime("%-m"),
            "month_name": obj.date.strftime("%B"),
            "day": obj.date.strftime("%-d"),
            "year": obj.date.strftime("%Y"),
        }

    def get_fast(self, obj):
        return {
            "fast_day": obj.fast_day,
            "fast_day_description": obj.FAST_DAYS_RANKS[obj.fast_day],
            "fast_day_reason": obj.fast_day_reasons,
        }

    def get_mass_readings(self, obj):
        return [{"citation": reading.long_citation, "text": reading.long_text} for reading in obj.mass_readings]

    def get_primary_color(self, obj):
        try:
            if obj.all:
                return obj.all[0].color.lower()
        except (KeyError, AttributeError):
            return None

    def get_primary_evening_color(self, obj):
        try:
            if obj.all_evening:
                return obj.all_evening[0].color.lower()
        except (KeyError, AttributeError):
            return self.get_primary_color(obj)

    def get_primary_feast(self, obj):
        try:
            if obj.all:
                return obj.all[0].name
        except (KeyError, AttributeError):
            return None

    def get_primary_evening_feast(self, obj):
        try:
            if obj.all:
                return obj.all_evening[0].name
        except (KeyError, AttributeError):
            return None

    def get_major_feast(self, obj):
        try:
            if obj.required:
                return obj.required[0].name
        except (KeyError, AttributeError):
            return None
        return None

    def get_major_or_minor_feast(self, obj):
        try:
            for feast in obj.all:
                if "FERIA" not in feast.rank.name:
                    return feast.name
        except (KeyError, AttributeError):
            return None
        return None
