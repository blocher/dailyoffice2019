from uuid import UUID

from django.db.models import Prefetch, Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from office.api.serializers import (
    CollectSerializer,
    PsalmSerializer,
    PsalmTopicSerializer,
    AboutItemSerializer,
    CollectTagCategorySerializer,
    ScriptureSerializer,
    SourceSerializer,
)
from office.models import Collect, AboutItem, CollectTagCategory, CollectTag, Scripture
from psalter.models import Psalm, PsalmTopicPsalm, PsalmVerse, PsalmTopic


class AboutViewSet(ViewSet):
    queryset = AboutItem.objects.order_by("order").all()
    serializer_class = AboutItemSerializer

    def list(self, request):
        about_items = self.queryset
        serializer = AboutItemSerializer(about_items, many=True)
        return Response(serializer.data)


class CollectsViewSet(ViewSet):
    queryset = (
        Collect.objects.order_by("collect_type__order", "order")
        .select_related("collect_type")
        .prefetch_related("tags__collect_tag_category")
        .all()
    )
    serializer_class = CollectSerializer

    def list(self, request):
        collects = self.queryset
        serializer = CollectSerializer(collects, many=True)
        return Response(serializer.data)


class GroupedCollectsViewSet(ViewSet):
    queryset = (
        Collect.objects.order_by("collect_type__order", "order")
        .select_related("collect_type")
        .prefetch_related("tags__collect_tag_category")
        .all()
    )

    def list(self, request):
        collects = self.queryset
        collect_tags = CollectTag.objects.select_related("collect_tag_category").order_by("order").all()
        sources = [collect_tag for collect_tag in collect_tags if collect_tag.collect_tag_category.key == "source"]

        themes = list(filter(lambda tag: tag.collect_tag_category.key == "theme", collect_tags))
        seasons = list(filter(lambda tag: tag.collect_tag_category.key == "season", collect_tags))
        commemoration_types = list(
            filter(lambda tag: tag.collect_tag_category.key == "commemoration_type", collect_tags)
        )
        liturgies = list(filter(lambda tag: tag.collect_tag_category.key in ["liturgy", "liturgical"], collect_tags))

        for source in sources:
            if source.key == "occasional":
                source.subcategories = []
                for theme in themes:
                    subcategory = theme
                    subcategory.collects = [
                        collect for collect in collects if theme in collect.tags.all() and source in collect.tags.all()
                    ]
                    if subcategory.collects:
                        source.subcategories.append(subcategory)
            if source.key == "year":
                source.subcategories = []
                for season in seasons:
                    subcategory = season
                    subcategory.collects = [
                        collect
                        for collect in collects
                        if season in collect.tags.all() and source in collect.tags.all()
                    ]
                    if subcategory.collects:
                        source.subcategories.append(subcategory)
                for commemoration_type in commemoration_types:
                    subcategory = commemoration_type
                    if subcategory.key in ["sunday", "major_feast"]:
                        continue
                    subcategory.collects = [
                        collect
                        for collect in collects
                        if commemoration_type in collect.tags.all() and source in collect.tags.all()
                    ]
                    if subcategory.collects:
                        source.subcategories.append(subcategory)
            if source.key == "liturgical":
                source.subcategories = []
                for liturgy in liturgies:
                    subcategory = liturgy
                    subcategory.collects = [
                        collect
                        for collect in collects
                        if liturgy in collect.tags.all() and source in collect.tags.all()
                    ]
                    if subcategory.collects:
                        source.subcategories.append(subcategory)

        serializer = SourceSerializer(sources, many=True)
        return Response(serializer.data)


class CollectCategoryViewSet(ViewSet):
    queryset = (
        CollectTagCategory.objects.order_by("order", "name")
        .prefetch_related(
            Prefetch("collecttag_set", queryset=CollectTag.objects.order_by("order", "name"), to_attr="tags")
        )
        .all()
    )
    serializer_class = CollectTagCategorySerializer

    def list(self, request):
        categories = self.queryset
        serializer = CollectTagCategorySerializer(categories, many=True)
        return Response(serializer.data)


class PsalmsViewSet(ViewSet):
    queryset = Psalm.objects.order_by("number").prefetch_related(
        Prefetch(
            "psalmtopicpsalm_set",
            queryset=PsalmTopicPsalm.objects.order_by("psalm_topic__order)").select_related("psalm_topic"),
            to_attr="topics",
        ),
        Prefetch("psalmverse_set", PsalmVerse.objects.order_by("number"), to_attr="verses"),
    )
    serializer_class = PsalmSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            uuid_obj = UUID(kwargs["pk"], version=4)
            psalm = self.queryset.filter(Q(pk=kwargs["pk"])).first()
        except ValueError:
            psalm = self.queryset.filter(Q(number=kwargs["pk"])).first()
        serializer = PsalmSerializer(psalm, many=False)
        return Response(serializer.data)

    def list(self, request):
        psalms = self.queryset
        serializer = PsalmSerializer(psalms, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def topics(self, request):
        topics = PsalmTopic.objects.order_by("order").all()
        serializer = PsalmTopicSerializer(topics, many=True)
        return Response(serializer.data)


class ScriptureViewSet(ViewSet):
    queryset = Scripture.objects.all()
    serializer_class = ScriptureSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            uuid_obj = UUID(kwargs["pk"], version=4)
            scripture = self.queryset.filter(Q(pk=kwargs["pk"])).first()
        except ValueError:
            scripture = self.queryset.filter(Q(passage=kwargs["pk"])).first()
        serializer = ScriptureSerializer(scripture, many=False)
        return Response(serializer.data)


class CanticlesViewSet(ViewSet):
    queryset = Scripture.objects.all()
    serializer_class = ScriptureSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            uuid_obj = UUID(kwargs["pk"], version=4)
            scripture = self.queryset.filter(Q(pk=kwargs["pk"])).first()
        except ValueError:
            scripture = self.queryset.filter(Q(passage=kwargs["pk"])).first()
        serializer = ScriptureSerializer(scripture, many=False)
        return Response(serializer.data)
