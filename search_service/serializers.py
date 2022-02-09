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

from .models import (
    Indexables,
    JSONResource,
)


logger = logging.getLogger(__name__)

utc = pytz.UTC


class IndexablesSummarySerializer(serializers.HyperlinkedModelSerializer):
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
        model = Indexables
        fields = [
            "type",
            "subtype",
            "group_id",
            "snippet",
            "language",
            "rank",
            "bounding_boxes",
        ]


class BaseModelToIndexablesSerializer(serializers.Serializer):
    @property
    def data(self):
        """Bypasses the wrapping of the returned value with a ReturnDict from the serializers.Serializer data method.
        This allows the serializer to return a list of items from an individual instance.
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
            indexables_data.append({**resource_fields, **indexable})
        return indexables_data


class IndexablesCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indexables
        fields = "__all__"


class IndexablesSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Indexables, i.e. the indexed objects that are used to
    drive search and which are associated with a IIIF resource
    """

    class Meta:
        model = Indexables
        fields = [
            "url",
            "resource_id",
            "content_id",
            "original_content",
            "group_id",
            "indexable",
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
            Indexables.objects.filter(
                resource_id=resource_id, content_id=content_id
            ).delete()
        return super(IndexablesSerializer, self).create(validated_data)


class AutocompleteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Indexables for autocompletion
    """

    class Meta:
        model = Indexables
        fields = [
            "indexable",
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


class JSONResourceToIndexablesSerializer(BaseModelToIndexablesSerializer):
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


# class IIIFSearchSummarySerializer(serializers.HyperlinkedModelSerializer):
#     """
#     Serializer that produces the summarized search results.
#     """

#     contexts = ContextSummarySerializer(read_only=True, many=True)
#     hits = serializers.SerializerMethodField("get_hits")
#     has_matching_parts = serializers.SerializerMethodField("get_has_matching_parts")
#     # resource_id = serializers.CharField(source="madoc_id", read_only=True)
#     resource_id = MadocIDSiteURNField(source="madoc_id", read_only=True)
#     resource_type = serializers.CharField(source="type")
#     rank = serializers.SerializerMethodField("get_rank")
#     sortk = serializers.SerializerMethodField("get_sortk")
#     metadata = serializers.SerializerMethodField("get_metadata")
#     rights = serializers.URLField()
#     provider = serializers.JSONField()
#     requiredStatement = serializers.JSONField()

# def get_sortk(self, iiif):
#     """
#     Generate a sort key to associate with the object.
#     """
#     order_key = None
#     if self.context.get("request"):
#         order_key = self.context["request"].data.get("sort_order", None)
#     if not order_key:
#         return self.get_rank(iiif=iiif)
#     logger.debug(f"Order key {order_key}")
#     if (
#         isinstance(order_key, dict)
#         and order_key.get("type")
#         and order_key.get("subtype")
#     ):
#         val = order_key.get("value_for_sort", "indexable")
#         sort_qs = (
#             Indexables.objects.filter(
#                 iiif=iiif,
#                 type__iexact=order_key.get("type"),
#                 subtype__iexact=order_key.get("subtype"),
#             )
#             .values(val)
#             .first()
#         )
#         if sort_qs:
#             sort_keys = list(sort_qs.values())[0]
#             return sort_keys
#     else:
#         logger.debug("We have no type or subtype on order key")
#     return self.get_sort_default(order_key=order_key)

# @staticmethod
# def get_sort_default(order_key):
#     if value_for_sort := order_key.get("value_for_sort"):
#         if value_for_sort.startswith("indexable_int"):
#             return 0
#         elif value_for_sort.startswith("indexable_float"):
#             return 0.0
#         elif value_for_sort.startswith("indexable_date"):
#             return datetime.min.replace(tzinfo=utc)
#         else:
#             return ""

#     if order_key.get("type") and order_key.get("subtype"):
#         return ""

#     return 0.0

# def get_rank(self, iiif):
#     """
#     Serializer method that calculates the average rank from the hits associated
#     with this search result
#     """
#     try:
#         return max([h["rank"] for h in self.get_hits(iiif=iiif)])
#     except TypeError or ValueError:
#         return 1.0

# def get_has_matching_parts(self, iiif):
#     if self.context.get("request"):
#         if self.context["request"].data.get("contains_hit_kwargs"):
#             qs = (
#                 Indexables.objects.filter(
#                     **self.context["request"].data["contains_hit_kwargs"],
#                     iiif__contexts__associated_iiif__madoc_id=iiif.madoc_id,
#                 )
#                 .distinct()
#                 .values(
#                     part_id=F("iiif__id"),
#                     part_label=F("iiif__label"),
#                     part_madoc_id=F("iiif__madoc_id"),
#                     part_type=F("iiif__type"),
#                     part_first_canvas_id=F("iiif__first_canvas_id"),
#                     part_thumbnail=F("iiif__madoc_thumbnail"),
#                 )
#             )
#             logger.debug(
#                 f"Contains queryset {self.context['request'].data['contains_hit_kwargs']}"
#             )
#             if qs:
#                 return qs

# def get_hits(self, iiif):
#     """
#     Serializer method that calculates the hits to return along with this search
#     result
#     """
#     # Rank must be greater than 0 (i.e. this is some kind of hit)
#     filter_kwargs = {"rank__gt": 0.0}
#     # Filter the indexables to query against to just those associated with this IIIF resource
#     qs = Indexables.objects.filter(iiif=iiif)
#     search_query = None
#     if self.context.get("request"):
#         if self.context["request"].data.get("hits_filter_kwargs"):
#             # We have a dictionary of queries to use, so we use that
#             search_query = (
#                 self.context["request"]
#                 .data["hits_filter_kwargs"]
#                 .get("search_vector", None)
#             )
#         else:
#             # Otherwise, this is probably a simple GET request, so we construct the queries from params
#             search_string = self.context["request"].query_params.get(
#                 "fulltext", None
#             )
#             language = self.context["request"].query_params.get(
#                 "search_language", None
#             )
#             search_type = self.context["request"].query_params.get(
#                 "search_type", "websearch"
#             )
#             if search_string:
#                 if language:
#                     search_query = SearchQuery(
#                         search_string, config=language, search_type=search_type
#                     )
#                 else:
#                     search_query = SearchQuery(
#                         search_string, search_type=search_type
#                     )
#             else:
#                 search_query = None
#     if search_query:
#         # Annotate the results in the queryset with rank, and with a snippet
#         qs = (
#             qs.annotate(
#                 rank=SearchRank(
#                     F("search_vector"), search_query, cover_density=True
#                 ),
#                 snippet=Concat(
#                     Value("'"),
#                     SearchHeadline(
#                         "original_content",
#                         search_query,
#                         max_words=50,
#                         min_words=25,
#                         max_fragments=3,
#                     ),
#                     output_field=CharField(),
#                 ),
#                 fullsnip=SearchHeadline(
#                     "indexable",
#                     search_query,
#                     start_sel="<start_sel>",
#                     stop_sel="<end_sel>",
#                     highlight_all=True,
#                 ),
#             )
#             .filter(search_vector=search_query, **filter_kwargs)
#             .order_by("-rank")
#         )
#     else:
#         return
#     # Use the Indexables summary serializer to return the hit list
#     serializer = IndexablesSummarySerializer(instance=qs, many=True)
#     return serializer.data

# def get_metadata(self, iiif):
#     """If the context has had the `metadata_fields` property set
#     by the calling view's `get_serializer_context`, then return only
#     the metdata items defined by this configuration. The metadata_fields
#     config object should be as follows:
#     metadata_fields = {lang_code: [label1, label2]}
#     e.g.
#     metadata_fields = {'en': ['Author', 'Collection']}

#     If metadata_fields has not been set, then all the metadata associated
#     with the iiif object is returned.
#     """
#     if self.context.get("request"):
#         if metadata_fields := self.context["request"].data.get("metadata_fields"):
#             logger.debug("We have metadata fields on the incoming request")
#             logger.debug(f"{metadata_fields}")
#             filtered_metadata = []
#             if iiif.metadata:
#                 for metadata_item in iiif.metadata:
#                     for lang, labels in metadata_fields.items():
#                         for label in labels:
#                             if label in metadata_item.get("label", {}).get(
#                                 lang, []
#                             ):
#                                 filtered_metadata.append(metadata_item)
#             return filtered_metadata
#     return iiif.metadata

# class Meta:
#     model = IIIFResource
#     fields = [
#         "url",
#         "resource_id",
#         "resource_type",
#         "madoc_thumbnail",
#         "thumbnail",
#         "id",
#         "rank",
#         "label",
#         "contexts",
#         "hits",
#         "sortk",
#         "metadata",
#         "first_canvas_id",
#         "has_matching_parts",
#         "rights",
#         "provider",
#         "requiredStatement",
#     ]
#     extra_kwargs = {
#         "url": {"view_name": "api:search_service:iiif-detail", "lookup_field": "id"}
#     }


class ContentObjectRelatedField(serializers.RelatedField):
    """
    A custom field to serialize generic relations
    """

    def to_representation(self, object):
        object_app = object._meta.app_label
        object_name = object._meta.object_name
        serializer_module_path = f'{object_app}.serializers.{object_name}Serializer'
        serializer_class = import_string(serializer_module_path)
        return serializer_class(object).data


class IndexablesResultSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Indexables with the snippets and ranks included
    """
    rank = serializers.FloatField()
    snippet = serializers.CharField()
    fullsnip = serializers.CharField()

    class Meta:
        model = Indexables
        fields = [
            "url",
            "resource_id",
            "content_id",
            "original_content",
            "group_id",
            "indexable",
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
            "fullsnip"
        ]
        extra_kwargs = {
            "url": {
                "view_name": "api:search_service:indexables-detail",
                "lookup_field": "id",
            }
        }


class JSONSearchSerializer(serializers.ModelSerializer):
    rank = serializers.FloatField()  # Not this isn't ranking the highest (yet)
    snippet = serializers.CharField()

    class Meta:
        model = JSONResource
        fields = [
            "id",
            "created",
            "modified",
            "label",
            "data",
            "rank",
            "snippet"
        ]