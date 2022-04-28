# Django Imports

import logging
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType

# DRF Imports
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

# Local imports
from .models import (
    Indexable,
    ResourceRelationship,
    JSONResource,
)

from .parsers import SearchParser, IndexableSearchParser
from .pagination import MadocPagination
from .serializers import (
    JSONResourceSerializer,
    JSONResourceRelationshipSerializer,
    ResourceRelationshipSerializer,
    IndexableSerializer,
    IndexableResultSerializer,
    JSONSearchSerializer,
    AutocompleteSerializer,
    ContentTypeAPISerializer,
    FacetedSearchQueryParamDataSerializer,
)
from .utils import ActionBasedSerializerMixin

from .filters import (
    GenericFilter,
    ResourceFilter,
    FacetFilter,
    GenericFacetListFilter,
    RankSnippetFilter,
)
from .settings import search_service_settings

logger = logging.getLogger(__name__)


class JSONResourceAPIViewSet(viewsets.ModelViewSet):
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


class IndexableAPIViewSet(viewsets.ModelViewSet):
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


class ResourceRelationshipAPIViewSet(viewsets.ModelViewSet):
    queryset = ResourceRelationship.objects.all()
    serializer_class = ResourceRelationshipSerializer
    lookup_field = "id"


class ContentTypeAPIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeAPISerializer
    lookup_field = "id"


class QueryParamDataMixin(object):
    """
    Gets the request's query params, effect a transform using
    the serializer provided as `query_param_serializer`,
    parse the transformed data with the parsers defined in
    `parsers_classes`, and update the request `data`
    property with the parsed data.

    The parsers provided in `parsers_classes` must define a
    `parse_data` method
    """

    query_param_serializer_class = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.query_params and self.query_param_serializer_class:
            logger.debug(
                f"Serialising query_params to parsable data: ({self.query_param_serializer_class}, {request.query_params})"
            )
            query_serializer = self.query_param_serializer_class(
                dict(request.query_params)
            )
            parsers = self.get_parsers()
            for p in parsers:
                if hasattr(p, "parse_data"):
                    logger.debug(
                        f"Parsing serialised data: ({p.__class__}, {query_serializer.data})"
                    )
                    request.data.update(p.parse_data(query_serializer.data))


class BaseSearchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    BaseClass for Search Service APIs.
    """

    lookup_field = "id"
    queryset = Indexable.objects.all().distinct()
    parser_classes = [SearchParser]
    permission_classes = [AllowAny]
    filter_backends = [GenericFilter]
    serializer_class = IndexableResultSerializer

    def create(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class GenericSearchBaseViewSet(QueryParamDataMixin, BaseSearchViewSet):
    query_param_serializer_class = FacetedSearchQueryParamDataSerializer
    pass


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


class JSONResourceSearchViewSet(GenericSearchBaseViewSet):
    """ """

    queryset = JSONResource.objects.all().distinct()
    parser_classes = [IndexableSearchParser]
    lookup_field = "id"
    permission_classes = [AllowAny]
    filter_backends = [ResourceFilter, FacetFilter, RankSnippetFilter]
    serializer_class = JSONSearchSerializer
