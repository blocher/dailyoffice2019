# Serializers define the API representation.
from rest_framework import serializers

from office.models import UpdateNotice, Collect, AboutItem, CollectTag, CollectTagCategory, Scripture
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
    title_and_tags = serializers.SerializerMethodField()

    def get_title_and_tags(self, obj):
        return obj.title + " " + " ".join([tag.name for tag in obj.tags.all()])

    class Meta:
        model = Collect
        fields = [
            "uuid",
            "title",
            "text",
            "traditional_text",
            "spanish_title",
            "spanish_text",
            "spanish_attribution",
            "order",
            "number",
            "page_number",
            "attribution",
            "tags",
            "title_and_tags",
        ]


class SubcategorySerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    name = serializers.CharField()
    key = serializers.CharField()
    order = serializers.IntegerField()
    collects = CollectSerializer(many=True, read_only=True)

    class Meta:
        fields = ["uuid", "key", "name", "order", "collects"]


class SourceSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    key = serializers.CharField()
    name = serializers.CharField()
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        fields = ["uuid", "key", "name", "subcategories"]


class PsalmVerseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PsalmVerse
        fields = [
            "id",
            "number",
            "first_half",
            "second_half",
            "first_half_tle",
            "second_half_tle",
            "first_half_spanish",
            "second_half_spanish",
        ]


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


class ScriptureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Scripture
        fields = ["uuid", "passage", "esv", "kjv", "rsv", "nvi"]
