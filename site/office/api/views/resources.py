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
)
from office.models import Collect, AboutItem, CollectTagCategory, CollectTag
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
