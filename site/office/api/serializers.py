# Serializers define the API representation.
from rest_framework import serializers

from office.models import UpdateNotice, Collect
from psalter.models import Psalm, PsalmVerse, PsalmTopic


class UpdateNoticeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UpdateNotice
        fields = ["uuid", "notice", "app_mode", "web_mode", "version"]


class CollectSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.CharField(source="collect_category.order")
    category_name = serializers.CharField(source="collect_category.name")

    class Meta:
        model = Collect
        fields = ["uuid", "title", "text", "order", "category", "category_name", "collect_type", "attribution"]


class PsalmVerseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PsalmVerse
        fields = ["id", "number", "first_half", "second_half"]


class PsalmTopicSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PsalmTopic
        fields = ["id", "topic_name", "psalms"]


class PsalmSerializer(serializers.HyperlinkedModelSerializer):
    topics = serializers.SerializerMethodField()
    verses = PsalmVerseSerializer(many=True, read_only=True)

    def get_topics(self, obj):
        topics = obj.topics
        topics = [PsalmTopicSerializer(topic.psalm_topic).data for topic in topics]
        return topics

    class Meta:
        model = Psalm
        fields = ["id", "number", "latin_title", "topics", "verses"]


class PsalmTopicSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PsalmTopic
        fields = ["id", "topic_name", "order"]
