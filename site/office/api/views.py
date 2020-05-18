from django.views.generic.base import TemplateResponseMixin
from rest_framework import viewsets
from rest_framework.generics import ListAPIView

from office.api.serializers import UpdateNoticeSerializer
from office.models import UpdateNotice


class UpdateNoticeView(TemplateResponseMixin, ListAPIView):
    queryset = UpdateNotice.objects.all()
    serializer_class = UpdateNoticeSerializer

    # def get_queryset(self):
    #     queryset = UpdateNotice.objects.order_by("-version", "-created")
    #     mode = self.request.path.split('/').pop()
    #     if mode == 'web':
    #         queryset = queryset.filter(web_mode=True)
    #     if mode == 'app':
    #         queryset = queryset.filter(app_mode=True)
    #     return queryset.all()
