"""
search_service/serializers/fields.py - Fields for search service types and relations. 
"""
import logging

from rest_framework import (
    serializers,
    relations,
)

from ..models import (
    Context,
)

logger = logging.getLogger(__name__)


class ContextsField(serializers.SlugRelatedField):
    """Contexts on an Indexable or Resource are serialized
    out to a list of urns, and in to a list of Context objects.
    When used as a writable serializer will carry out a get_or_create,
    and can be provided with either a urn string, or a dict with `urn`
    and `type` keys.
    If just a urn string is provided, the type will be derived from the urn.
    """

    queryset = Context.objects.all()

    def to_internal_value(self, data):
        if isinstance(data, str):
            context_type = data.split(":")[2]
            context_data = {self.slug_field: data, "type": context_type}
        else:
            context_data = data
        queryset = self.get_queryset()
        try:
            return queryset.get_or_create(**context_data)[0]
        except (TypeError, ValueError):
            self.fail("invalid")
