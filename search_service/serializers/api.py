"""
search_service/serializers/api.py - Serializer classes for API views
"""

import logging

from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from ..models import (
    Indexable,
    ResourceRelationship,
    BaseSearchResource,
    JSONResource,
)


logger = logging.getLogger(__name__)


class ContentTypeAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = [
            "id",
            "app_label",
            "model",
        ]


class JSONResourceAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = JSONResource
        fields = [
            "id",
            "created",
            "modified",
            "label",
            "data",
        ]


class ResourceRelationshipAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceRelationship
        fields = "__all__"


class IndexableAPISerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Indexable, i.e. the indexed objects that are used to
    drive search and which are associated with a IIIF resource
    """

    class Meta:
        model = Indexable
        fields = [
            "url",
            "resource_id",
            "content_id",
            "original_content",
            "group_id",
            "indexable_text",
            "indexable_date_range_start",
            "indexable_date_range_end",
            "indexable_int",
            "indexable_float",
            "indexable_json",
            "selector",
            "type",
            "subtype",
            "language_iso639_2",
            "language_iso639_1",
            "language_display",
            "language_pg",
            "search_vector",
        ]
        extra_kwargs = {
            "url": {
                "view_name": "api:search_service:indexable-detail",
                "lookup_field": "id",
            }
        }

    def create(self, validated_data):
        # On create, associate the resource with the relevant IIIF resource
        # via the Madoc identifier for that object
        resource_id = validated_data.get("resource_id")
        content_id = validated_data.get("content_id")
        iiif = IIIFResource.objects.get(madoc_id=resource_id)
        validated_data["iiif"] = iiif
        if content_id and resource_id:
            print(
                f"Deleting any indexables for {resource_id} with content id {content_id}"
            )
            Indexable.objects.filter(
                resource_id=resource_id, content_id=content_id
            ).delete()
        return super(IndexableAPISerializer, self).create(validated_data)
