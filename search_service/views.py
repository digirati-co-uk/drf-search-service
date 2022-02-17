# Django Imports

import logging
from collections import defaultdict

from django_filters.rest_framework import DjangoFilterBackend

# DRF Imports
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


# Local imports
from .models import (
    Indexable,
    JSONResource,
)
from .parsers import IIIFSearchParser, SearchParser, JSONSearchParser
from .pagination import MadocPagination
from .serializers import (
    JSONResourceSerializer,
    JSONResourceRelationshipSerializer,
    ResourceRelationshipSerializer,
    IndexableSerializer,
    IndexableResultSerializer,
    JSONSearchSerializer,
    AutocompleteSerializer,
)
from .utils import ActionBasedSerializerMixin

from .filters import (
    FacetListFilter,
    GenericFilter,
    ResourceFilter,
    FacetFilter,
    GenericFacetListFilter,
    RankSnippetFilter,
)
from .settings import search_service_settings

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
    filter_backends = [ResourceFilter, FacetFilter, RankSnippetFilter]
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
