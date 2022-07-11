# Serializers define the API representation.
from rest_framework import serializers

from office.models import UpdateNotice, Collect, AboutItem, CollectTag, CollectTagCategory
from psalter.models import Psalm, PsalmVerse, PsalmTopic


class UpdateNoticeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UpdateNotice
        fields = ["uuid", "notice", "app_mode", "web_mode", "version"]


class AboutItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AboutItem
        fields = [
            "uuid",
            "question",
            "question_for_web",
            "question_for_app",
            "answer",
            "answer_for_web",
            "answer_for_app",
            "order",
            "mode",
            "app_mode",
            "web_mode",
        ]


class CollectTagSerializer(serializers.HyperlinkedModelSerializer):
    category_order = serializers.IntegerField(source="collect_tag_category.order")
    category_name = serializers.CharField(source="collect_tag_category.name")
    category_key = serializers.CharField(source="collect_tag_category.key")
    category_uuid = serializers.UUIDField(source="collect_tag_category.uuid")

    class Meta:
        model = CollectTag
        fields = ["uuid", "name", "category_order", "order", "key", "category_name", "category_key", "category_uuid"]


class CollectTagCategorySerializer(serializers.HyperlinkedModelSerializer):
    tags = CollectTagSerializer(many=True, read_only=True)

    class Meta:
        model = CollectTagCategory
        fields = ["uuid", "name", "key", "order", "tags"]


class CollectSerializer(serializers.HyperlinkedModelSerializer):
    tags = CollectTagSerializer(many=True, read_only=True)

    class Meta:
        model = Collect
        fields = ["uuid", "title", "text", "traditional_text", "order", "number", "attribution", "tags"]


class PsalmVerseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PsalmVerse
        fields = ["id", "number", "first_half", "second_half", "first_half_tle", "second_half_tle"]


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
