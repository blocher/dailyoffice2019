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
    season = SeasonSerializer()
    commemorations = CommemorationSerializer(many=True, source="all")
