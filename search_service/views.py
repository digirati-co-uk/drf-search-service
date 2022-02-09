# Django Imports

import itertools
import logging
from collections import defaultdict

from django.db import models
from django.utils.translation import get_language
from django_filters.rest_framework import DjangoFilterBackend

# DRF Imports
from rest_framework import generics, filters, status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, ParseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


# Local imports
from .models import (
    Indexable,
    JSONResource,
)
from .parsers import IIIFSearchParser, SearchParser, JSONSearchParser
from .pagination import MadocPagination
from .serializer_utils import ActionBasedSerializerMixin
from .serializers import (
    JSONResourceSerializer,
    JSONResourceRelationshipSerializer,
    ResourceRelationshipSerializer,
    IndexableSerializer,
    IndexableResultSerializer,
    JSONSearchSerializer,
    AutocompleteSerializer,
)

from .filters import (
    FacetListFilter,
    GenericFilter,
    JSONResourceFilter,
    GenericFacetListFilter,
)
from .indexable_utils import gen_indexables

from .settings import search_service_settings

# Globals
default_lang = get_language()
global_facet_on_manifests = search_service_settings.FACET_ON_MANIFESTS_ONLY
global_facet_types = ["metadata"]

logger = logging.getLogger(__name__)


class JSONResourceViewSet(viewsets.ModelViewSet):
    queryset = JSONResource.objects.all()
    serializer_class = JSONResourceSerializer
    lookup_field = "id"

    @action(detail=False, methods=["post"])
    def create_nested(self, request, *args, **kwargs):
        parent_serializer = self.get_serializer(data=request.data)
        parent_serializer.is_valid(raise_exception=True)
        self.perform_create(parent_serializer)

        child_resource_data = request.data.get("child_resources")
        child_serializer = self.get_serializer(data=child_resource_data, many=True)
        child_serializer.is_valid(raise_exception=True)
        self.perform_create(child_serializer)

        relationships = [
            {
                "source": child.get("id"),
                "target": parent_serializer.data.get("id"),
                "type": "part_of",
            }
            for child in child_serializer.data
        ]
        relations_serializer = JSONResourceRelationshipSerializer(
            relationships, many=True
        )
        indexed_relations_serializer = ResourceRelationshipSerializer(
            data=relations_serializer.data, many=True
        )
        indexed_relations_serializer.is_valid(raise_exception=True)
        indexed_relations_serializer.save()
        headers = self.get_success_headers(parent_serializer.data)
        return Response(
            [parent_serializer.data]
            + child_serializer.data
            + indexed_relations_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class IndexableViewSet(viewsets.ModelViewSet):
    queryset = Indexable.objects.all()
    serializer_class = IndexableSerializer
    lookup_field = "id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "resource_id",
        "content_id",
        "type",
        "subtype",
    ]


# class SearchBaseClass(viewsets.ReadOnlyModelViewSet):
#     """
#     BaseClass for Search Service APIs.
#     """
#
#     queryset = Indexable.objects.all().distinct()
#     parser_classes = [IIIFSearchParser]
#     lookup_field = "id"
#     permission_classes = [AllowAny]


# class IIIFSearch(SearchBaseClass):
#     """
#     Simple read only view for the IIIF data with methods for
#     adding hits and generating facets for return in the results
#
#     Uses a custom paginator to fit the Madoc model.
#     """
#
#     filter_backends = [IIIFSearchFilter]
#     pagination_class = MadocPagination
#
#     def get_facets(self, request):
#         facet_summary = defaultdict(dict)
#         # If we haven't been provided a list of facet fields via a POST
#         # just generate the list by querying the unique list of metadata subtypes
#         # Make a copy of the query so we aren't running the get_queryset logic every time
#         facetable_queryset = self.filter_queryset(queryset=self.get_queryset())
#         if request.data.get("facet_on_manifests", None):
#             """
#             Facet on IIIF objects where:
#
#              1. They are associated (via the reverse relationship on `contexts`) with the queryset,
#                 and where the associated context is a manifest
#              2. The object type is manifest
#
#              In other words, give me all the manifests where they are associated with a manifest context
#               that is related to the objects in the queryset. This manifest context should/will be
#               themselves as manifests are associated with themselves as context.
#             """
#             facetable_q = self.queryset.filter(
#                 contexts__associated_iiif__madoc_id__in=facetable_queryset,
#                 contexts__type__iexact="manifest",
#                 type__iexact="manifest",
#             ).distinct()
#         else:
#             """
#             Otherwise, just create the facets on the objects that are in the queryset, rather than their
#             containing manifest contexts.
#             """
#             facetable_q = facetable_queryset
#         # if not request.data.get("facet_types", None):
#         #     request.data["facet_types"] = ["metadata"]
#         # if request.data.get("facet_fields"):
#         #     facet_summary = (
#         #         facetable_q.filter(
#         #             indexables__type__in=request.data["facet_types"],
#         #             indexables__subtype__in=request.data["facet_fields"],
#         #         )
#         #         .values("indexables__type", "indexables__subtype", "indexables__indexable")
#         #         .annotate(n=models.Count("pk", distinct=True))
#         #         .order_by("indexables__type", "indexables__subtype", "-n", "indexables__indexable")
#         #     )
#         # else:
#         #     facet_summary = (
#         #         facetable_q.filter(indexables__type__in=request.data["facet_types"])
#         #         .values("indexables__type", "indexables__subtype", "indexables__indexable")
#         #         .annotate(n=models.Count("pk", distinct=True))
#         #         .order_by("indexables__type", "indexables__subtype", "-n", "indexables__indexable")
#         #     )
#         facet_filter_args = [
#             models.Q(
#                 indexables__type__in=request.data.get("facet_types", ["metadata"])
#             ),
#         ]
#         if facet_fields := request.data.get("facet_fields"):
#             facet_filter_args.append(models.Q(indexables__subtype__in=facet_fields))
#         if facet_languages := request.data.get("facet_languages"):
#             facet_language_codes = set(map(lambda x: x.split("-")[0], facet_languages))
#             iso639_1_codes = list(filter(lambda x: len(x) == 2, facet_language_codes))
#             iso639_2_codes = list(filter(lambda x: len(x) == 3, facet_language_codes))
#             # Always include indexables where no language is specified.
#             # This will be cases where there it has neither iso639 field set.
#             facet_language_filter = models.Q(
#                 indexables__language_iso639_1__isnull=True
#             ) & models.Q(indexables__language_iso639_2__isnull=True)
#             if iso639_1_codes:
#                 facet_language_filter |= models.Q(
#                     indexables__language_iso639_1__in=iso639_1_codes
#                 )
#             if iso639_2_codes:
#                 facet_language_filter |= models.Q(
#                     indexables__language_iso639_2__in=iso639_2_codes
#                 )
#             facet_filter_args.append(facet_language_filter)
#         facet_summary = (
#             facetable_q.filter(*facet_filter_args)
#             .values("indexables__type", "indexables__subtype", "indexables__indexable")
#             .annotate(n=models.Count("pk", distinct=True))
#             .order_by(
#                 "indexables__type", "indexables__subtype", "-n", "indexables__indexable"
#             )
#         )
#         grouped_facets = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
#         truncate_to = request.data.get("num_facets", 10)
#         truncated_facets = defaultdict(lambda: defaultdict(dict))
#         # Turn annotated list of results into a deeply nested dict
#         for facet in facet_summary:
#             grouped_facets[facet["indexables__type"]][facet["indexables__subtype"]][
#                 facet["indexables__indexable"]
#             ] = facet["n"]
#         # Take the deeply nested dict and truncate the leaves of the tree to just N keys.
#         for facet_type, facet_subtypes in grouped_facets.items():
#             for k, v in facet_subtypes.items():
#                 truncated_facets[facet_type][k] = dict(
#                     itertools.islice(v.items(), truncate_to)
#                 )
#         return truncated_facets
#
#     def list(self, request, *args, **kwargs):
#         resp = super().list(request, *args, **kwargs)
#         resp.data.update({"facets": self.get_facets(request=request)})
#         reverse_sort = False
#         if request.data.get("sort_order", None):
#             if (direction := request.data["sort_order"].get("direction")) is not None:
#                 if direction == "descending":
#                     logger.debug("Descending")
#                     reverse_sort = True
#         resp.data["results"] = sorted(
#             resp.data["results"],
#             key=lambda k: (k.get("sortk"),),
#             reverse=reverse_sort,
#         )
#         return resp


# class Facets(SearchBaseClass):
#     """
#     Simple read only view to return a list of facet fields
#     """
#
#     filter_backends = [FacetListFilter]
#
#     def get_facet_list(self, request):
#         facet_dict = defaultdict(list)
#         # If we haven't been provided a list of facet fields via a POST
#         # just generate the list by querying the unique list of metadata subtypes
#         # Make a copy of the query so we aren't running the get_queryset logic every time
#         facetable_queryset = self.filter_queryset(queryset=self.get_queryset())
#         if request.data.get("facet_on_manifests", None):
#             """
#             Facet on IIIF objects where:
#
#              1. They are associated (via the reverse relationship on `contexts`) with the queryset,
#                 and where the associated context is a manifest
#              2. The object type is manifest
#
#              In other words, give me all the manifests where they are associated with a manifest
#              context that is related to the objects in the queryset. This manifest context
#              should/will be themselves as manifests are associated with themselves as context.
#             """
#             facetable_q = IIIFResource.objects.filter(
#                 contexts__associated_iiif__madoc_id__in=facetable_queryset,
#                 contexts__type__iexact="manifest",
#                 type__iexact="manifest",
#             ).distinct()
#         else:
#             """
#             Otherwise, just create the facets on the objects that are in the queryset,
#             rather than their containing manifest contexts.
#             """
#             facetable_q = facetable_queryset
#         facet_fields = []
#         if not request.data.get("facet_types", None):
#             request.data["facet_types"] = ["metadata"]
#         for facet_type in request.data["facet_types"]:
#             for t in (
#                 facetable_q.filter(indexables__type__iexact=facet_type)
#                 .values("indexables__subtype")
#                 .distinct()
#             ):
#                 for _, v in t.items():
#                     if v and v != "":
#                         facet_fields.append((facet_type, v))
#         facet_l = sorted(list(set(facet_fields)))
#         for i in facet_l:
#             facet_dict[i[0]].append(i[1])
#         return facet_dict
#
#     def list(self, request, *args, **kwargs):
#         response = super(Facets, self).list(request, args, kwargs)
#         response.data = self.get_facet_list(request=request)
#         return response
#
#


class GenericSearchBaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    BaseClass for Search Service APIs.
    """

    queryset = Indexable.objects.all().distinct()
    parser_classes = [SearchParser]
    lookup_field = "id"
    permission_classes = [AllowAny]
    filter_backends = [GenericFilter]
    serializer_class = IndexableResultSerializer

    def create(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class JSONResourceSearchViewSet(GenericSearchBaseViewSet):
    """ """

    queryset = JSONResource.objects.all().distinct()
    parser_classes = [JSONSearchParser]
    lookup_field = "id"
    permission_classes = [AllowAny]
    filter_backends = [JSONResourceFilter]
    serializer_class = JSONSearchSerializer

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        return resp

    def create(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class GenericFacetsViewSet(GenericSearchBaseViewSet):
    """
    Simple read only view to return a list of facet fields
    """

    parser_classes = [SearchParser]
    filter_backends = [GenericFacetListFilter]
    serializer_class = IndexableSerializer

    def get_facet_list(self, request):
        facet_dict = defaultdict(list)
        # If we haven't been provided a list of facet fields via a POST
        # just generate the list by querying the unique list of metadata subtypes
        # Make a copy of the query so we aren't running the get_queryset logic every time
        facetable_q = self.filter_queryset(queryset=self.get_queryset())
        facet_fields = []
        if not request.data.get("facet_types", None):
            request.data["facet_types"] = ["metadata"]
        for facet_type in request.data["facet_types"]:
            for t in (
                facetable_q.filter(type__iexact=facet_type).values("subtype").distinct()
            ):
                for _, v in t.items():
                    if v and v != "":
                        facet_fields.append((facet_type, v))
        facet_l = sorted(list(set(facet_fields)))
        for i in facet_l:
            facet_dict[i[0]].append(i[1])
        return facet_dict

    def list(self, request, *args, **kwargs):
        response = super(GenericFacetsViewSet, self).list(request, args, kwargs)
        response.data = self.get_facet_list(request=request)
        logger.info("Facets")
        logger.info(self.get_facet_list(request=request))
        return response

    def create(self, request, *args, **kwargs):
        response = super(GenericFacetsViewSet, self).list(request, args, kwargs)
        response.data = self.get_facet_list(request=request)
        logger.info("Facets")
        logger.info(self.get_facet_list(request=request))
        return response
