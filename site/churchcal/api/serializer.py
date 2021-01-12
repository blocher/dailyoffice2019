from rest_framework import serializers

from office.morning_prayer import MorningPrayer


class RankSerializer(serializers.Serializer):
    name = serializers.CharField()
    formatted_name = serializers.CharField()
    precedence = serializers.IntegerField(source="precedence_rank")


class CommemorationSerializer(serializers.Serializer):
    name = serializers.CharField()
    rank = RankSerializer()
    colors = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()
    collects = serializers.SerializerMethodField()

    def get_colors(self, obj):
        colors = [obj.color, obj.additional_color, obj.alternate_color, obj.alternate_color_2]
        return [color.lower() for color in colors if color]

    def get_links(self, obj):
        links = [obj.link_1, obj.link_2, obj.link_3]
        return [link.lower() for link in links if link]

    def get_collects(self, obj):
        return {
            "collect": obj.morning_prayer_collect,
            "alternate_collect": obj.evening_prayer_collect
            if obj.evening_prayer_collect != obj.morning_prayer_collect
            else None,
            "vigil_collect": None if obj.eve_collect == "" else obj.eve_collect,
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
