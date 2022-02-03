import logging
from rest_framework import serializers

from search_service.serializers import BaseModelToIndexablesSerializer

from .models import (
    ExemplarResource,
)

logger = logging.getLogger(__name__)


class ExemplarResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExemplarResource
        fields = [
            "id",
            "created",
            "modified",
            "label",
            "data",
        ]


class ExemplarResourceToIndexablesSerializer(BaseModelToIndexablesSerializer):

    def to_indexables(self, instance):
        indexables = [
            {
                "type": "descriptive",
                "subtype": "label",
                "original_content": instance.label,
                "indexable": instance.label,
            }
        ]
        for k, v in instance.data.items():
            indexables.append(
                {
                    "type": "descriptive",
                    "subtype": k,
                    "original_content": v,
                    "indexable": v,
                }
            )

        return indexables
