"""
search_service/serializers/search.py - Serializer classes for Indexables and Resources for search viewsets.  
"""

import logging

from django.utils.module_loading import import_string
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from ..models import (
    Indexable,
    ResourceRelationship,
    BaseSearchResource,
    JSONResource,
)


logger = logging.getLogger(__name__)


def calc_offsets(obj):
    """
    The search "hit" should have a 'fullsnip' annotation which is a the entire
    text of the indexable resource, with <start_sel> and <end_sel> wrapping each
    highlighted word.

    Check if there's a selector on the indexable, and then if there's a box-selector
    use this to generate a list of xywh coordinates by retrieving the selector by
    its index from a list of lists
    """
    if hasattr(obj, "fullsnip"):
        words = obj.fullsnip.split(" ")
        offsets = []
        if words:
            for i, word in enumerate(words):
                if "<start_sel>" in word and "<end_sel>" in word:
                    offsets.append(i)
            if offsets:
                if obj.selector:
                    if (boxes := obj.selector.get("box-selector")) is not None:
                        box_list = []
                        for x in offsets:
                            try:
                                box_list.append(boxes[x])
                            except (IndexError, ValueError):
                                pass
                        if box_list:
                            return box_list  # [boxes[x] for x in offsets if boxes[x]]
                        else:
                            return
    return


class IndexableSummarySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that produces a summary of an individually indexed "field" or text
    resource for return in lists of results or other similar nested views
    """

    rank = serializers.FloatField(default=None, read_only=True)
    snippet = serializers.CharField(default=None, read_only=True)
    language = serializers.CharField(
        default=None, read_only=None, source="language_iso639_1"
    )
    bounding_boxes = serializers.SerializerMethodField()

    @staticmethod
    def get_bounding_boxes(obj):
        return calc_offsets(obj)

    class Meta:
        model = Indexable
        fields = [
            "type",
            "subtype",
            "group_id",
            "snippet",
            "language",
            "rank",
            "bounding_boxes",
        ]


class AutocompleteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Indexable for autocompletion
    """

    class Meta:
        model = Indexable
        fields = [
            "indexable_text",
        ]


class JSONResourceRelationshipSerializer(serializers.Serializer):
    def to_representation(self, relationship):
        json_resource_content_type = ContentType.objects.get_for_model(JSONResource).pk
        return {
            "source_id": relationship.get("source"),
            "source_content_type": json_resource_content_type,
            "target_id": relationship.get("target"),
            "target_content_type": json_resource_content_type,
            "type": relationship.get("type"),
        }


class BaseSearchResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseSearchResource
        fields = ["id", "created", "modified"]


class ContentObjectRelatedField(serializers.RelatedField):
    """
    A custom field to serialize generic relations
    """

    def to_representation(self, object):
        object_app = object._meta.app_label
        object_name = object._meta.object_name
        serializer_module_path = f"{object_app}.serializers.{object_name}Serializer"
        serializer_class = import_string(serializer_module_path)
        return serializer_class(object).data


class IndexableResultSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Indexable with the snippets and ranks included
    """

    rank = serializers.FloatField()
    snippet = serializers.CharField()
    fullsnip = serializers.CharField()

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
            "rank",
            "snippet",
            "fullsnip",
        ]
        extra_kwargs = {
            "url": {
                "view_name": "api:search_service:indexable-detail",
                "lookup_field": "id",
            }
        }


class JSONSearchSerializer(serializers.ModelSerializer):
    rank = serializers.FloatField(
        read_only=True
    )  # Not this isn't ranking the highest (yet)
    snippet = serializers.CharField(read_only=True)

    class Meta:
        model = JSONResource
        fields = [
            "id",
            "created",
            "modified",
            "label",
            "data",
            "rank",
            "snippet",
        ]
