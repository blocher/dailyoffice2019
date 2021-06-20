# Serializers define the API representation.
from rest_framework import serializers

from office.models import UpdateNotice


class UpdateNoticeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UpdateNotice
        fields = ["uuid", "notice", "app_mode", "web_mode", "version"]
