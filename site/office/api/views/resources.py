from uuid import UUID

from django.db.models import Prefetch, Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from office.api.serializers import CollectSerializer, PsalmSerializer, PsalmTopicSerializer
from office.models import Collect
from psalter.models import Psalm, PsalmTopicPsalm, PsalmVerse, PsalmTopic


class CollectsViewSet(ViewSet):
    queryset = Collect.objects.order_by("collect_category__order", "order").select_related("collect_category").all()
    serializer_class = CollectSerializer

    def list(self, request):
        collects = self.queryset
        serializer = CollectSerializer(collects, many=True)
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
