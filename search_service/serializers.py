import logging
import json
import itertools
from datetime import datetime
import pytz

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline
from django.db.models.functions import Concat
from django.db.models import F, Value, CharField
from django.utils.module_loading import import_string
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from .serializer_utils import calc_offsets


from .language.indexable import (
    format_indexable_language_fields,
)
from .models import (
    Indexable,
    ResourceRelationship,
    BaseSearchResource,
    JSONResource,
)


logger = logging.getLogger(__name__)

utc = pytz.UTC


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


class IndexableCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indexable
        fields = "__all__"


class IndexableSerializer(serializers.HyperlinkedModelSerializer):
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
                "view_name": "api:search_service:indexables-detail",
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
        return super(IndexableSerializer, self).create(validated_data)


class AutocompleteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Indexable for autocompletion
    """

    class Meta:
        model = Indexable
        fields = [
            "indexable_text",
        ]


class JSONResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = JSONResource
        fields = [
            "id",
            "created",
            "modified",
            "label",
            "data",
        ]


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


class ResourceRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceRelationship
        fields = "__all__"


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
                "view_name": "api:search_service:indexables-detail",
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
        fields = ["id", "created", "modified", "label", "data", "rank", "snippet"]
