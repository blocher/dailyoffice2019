import django
from django.db.models.fields.related import OneToOneField, OneToOneRel
from django.db.models.constants import LOOKUP_SEP


def _get_subclasses_recurse_without_managed(self, model, levels=None):
    """
    Given a Model class, find all related objects, exploring children
    recursively, returning a `list` of strings representing the
    relations for select_related
    """
    if django.VERSION < (1, 8):
        related_objects = model._meta.get_all_related_objects()
    else:
        related_objects = [f for f in model._meta.get_fields() if isinstance(f, OneToOneRel)]

    rels = [
        rel
        for rel in related_objects
        if isinstance(rel.field, OneToOneField)
        and issubclass(rel.field.model, model)
        and rel.field.model._meta.managed is not False
        and model is not rel.field.model
    ]

    subclasses = []
    if levels:
        levels -= 1
    for rel in rels:
        if levels or levels is None:
            for subclass in self._get_subclasses_recurse(rel.field.model, levels=levels):
                subclasses.append(rel.get_accessor_name() + LOOKUP_SEP + subclass)
        subclasses.append(rel.get_accessor_name())
    return subclasses


def get_queryset_as_subclasses(self):
    return self._queryset_class(self.model).select_subclasses()
