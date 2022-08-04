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


class RankSnippetSerializerMixin(metaclass=serializers.SerializerMetaclass):
    rank = serializers.FloatField(
        default=None, read_only=True
    )  # Not this isn't ranking the highest (yet)
    snippet = serializers.CharField(default=None, read_only=True)
    fullsnip = serializers.CharField(default=None, read_only=True)


class BaseRankSnippetSearchSerializer(
    RankSnippetSerializerMixin, serializers.HyperlinkedModelSerializer
):
    """
    Provides a Model serializer with access to the additional fields `rank`, `snippet`
    and `fullsnip` which are annotated to the queryset as part of search filtering.
    """

    pass


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


class IndexableAPISearchSerializer(BaseRankSnippetSearchSerializer):
    """
    Serializer for the Indexable with the snippets and ranks included
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


class IndexablePublicSearchSerializer(BaseRankSnippetSearchSerializer):
    """
    Serializer for the Indexable with the snippets and ranks included
    """

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
            "indexable_text",
            "snippet",
            "language",
            "rank",
            "bounding_boxes",
        ]


class JSONResourceAPISearchSerializer(BaseRankSnippetSearchSerializer):
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
        extra_kwargs = {
            "url": {
                "view_name": "api:search_service:jsonresource-detail",
                "lookup_field": "id",
            }
        }


class JSONResourcePublicSearchSerializer(
    RankSnippetSerializerMixin, serializers.ModelSerializer
):
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
