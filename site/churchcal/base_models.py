import uuid

from django.db import models
from django.db.models import DateTimeField, BooleanField
from django.db.models import UUIDField


class UUIDModel(models.Model):
    uuid = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class CreatableModel(models.Model):
    created = DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class UpdatableModel(models.Model):
    updated = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, CreatableModel, UpdatableModel):
    class Meta:
        abstract = True
