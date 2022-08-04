"""
search_service/serializers/indexing.py - Serializer classes to extract indexables from a Resource as part of an indexing task. 
"""

import logging

from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from ..language.indexable import (
    format_indexable_language_fields,
)
from ..models import (
    Namespace, 
    Indexable,
)

logger = logging.getLogger(__name__)


class IndexableCreateUpdateSerializer(serializers.ModelSerializer):
    namespaces = serializers.PrimaryKeyRelatedField(
        queryset=Namespace.objects.all(), many=True, allow_empty=True
    )

    class Meta:
        model = Indexable
        fields = "__all__"


class BaseModelToIndexableSerializer(serializers.Serializer):
    @property
    def data(self):
        """Bypasses the wrapping of the returned value with a ReturnDict from
        the serializers.Serializer data method.
        This allows the serializer to return a list of items from an
        individual instance.
        """
        if not hasattr(self, "_data"):
            self._data = self.to_representation(self.instance)
        return self._data

    def to_indexables(self, instance):
        return [{}]

    def to_representation(self, instance):
        resource_fields = {
            "resource_id": instance.id,
            "resource_content_type": ContentType.objects.get_for_model(instance).pk,
            "namespaces": [ns.id for ns in instance.namespaces.all()],
        }
        indexables_data = []
        for indexable in self.to_indexables(instance):
            indexable_language = format_indexable_language_fields(
                indexable.pop("language", None)
            )
            indexables_data.append(
                {**resource_fields, **indexable_language, **indexable}
            )
        return indexables_data


class JSONResourceToIndexableSerializer(BaseModelToIndexableSerializer):
    def to_indexables(self, instance):
        indexables = [
            {
                "type": "descriptive",
                "subtype": "label",
                "original_content": instance.label,
                "indexable_text": instance.label,
            }
        ]
        for k, v in instance.data.items():
            indexables.append(
                {
                    "type": "descriptive",
                    "subtype": k,
                    "original_content": v,
                    "indexable_text": v,
                }
            )

        return indexables
