# Django Django Imports

import logging
import itertools
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType

from django.db.models import (
    Count,
    Q,
)

# DRF Imports
from rest_framework import (
    status,
    viewsets,
    mixins,
)
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

# Local imports
from .models import (
    Context,
    Indexable,
    ResourceRelationship,
    JSONResource,
)

from .parsers import (
    SearchParser,
    IndexableSearchParser,
    ResourceSearchParser,
)
from .pagination import MadocPagination

from .serializers.api import (
    ContentTypeAPISerializer,
    ContextAPISerializer,
    JSONResourceAPISerializer,
    ResourceRelationshipAPISerializer,
    IndexableAPISerializer,
)
from .serializers.query_param import (
    FacetedSearchQueryParamDataSerializer,
)
from .serializers.search import (
    JSONResourceRelationshipSerializer,
    IndexableAPISearchSerializer,
    IndexablePublicSearchSerializer,
    JSONResourceAPISearchSerializer,
    JSONResourcePublicSearchSerializer,
    AutocompleteSerializer,
)
from .utils import ActionBasedSerializerMixin

from .filters import (
    GenericFilter,
    ResourceFilter,
    AuthContextsFilter,
    ContextsFilter,
    FacetFilter,
    GenericFacetListFilter,
    RankSnippetFilter,
)
from .authentication import (
    ContextsHeaderAuthentication,
)
from .settings import search_service_settings

logger = logging.getLogger(__name__)


class JSONResourceAPIViewSet(viewsets.ModelViewSet):
    queryset = JSONResource.objects.all()
    serializer_class = JSONResourceAPISerializer
    filter_backends = [AuthContextsFilter]
    filterset_fields = [
        "resource_id",
    ]
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
        indexed_relations_serializer = ResourceRelationshipAPISerializer(
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


class SandboxedJSONResourceAPIViewSet(JSONResourceAPIViewSet):
    authentication_classes = [ContextsHeaderAuthentication]


class IndexableAPIViewSet(viewsets.ModelViewSet):
    queryset = Indexable.objects.all()
    serializer_class = IndexableAPISerializer
    lookup_field = "id"
    filter_backends = [AuthContextsFilter, DjangoFilterBackend]
    filterset_fields = [
        "resource_id",
        "content_id",
        "type",
        "subtype",
    ]


class SandboxedIndexableAPIViewSet(IndexableAPIViewSet):
    authentication_classes = [ContextsHeaderAuthentication]


class ResourceRelationshipAPIViewSet(viewsets.ModelViewSet):
    queryset = ResourceRelationship.objects.all()
    serializer_class = ResourceRelationshipAPISerializer
    lookup_field = "id"


class ContextAPIViewSet(viewsets.ModelViewSet):
    queryset = Context.objects.all()
    serializer_class = ContextAPISerializer
    lookup_field = "urn"


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


class BaseSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Base class for search viewsets, implements only a `list` and `create`
    to allow for GET and POST searches. Detail views for models are to be
    implemented by other viewsets.
    """

    lookup_field = "id"
    parser_classes = [SearchParser]
    filter_backends = [AuthContextsFilter, GenericFilter]

    default_facets = ["metadata", "entity"]

    def get_facet_indexable_data(self, request, queryset):
        """Get"""
        facet_filters = [
            Q(resource_id__in=queryset),
            Q(type__in=request.data.get("facet_types", self.default_facets)),
        ]
        if facet_fields := request.data.get("facet_fields"):
            facet_filters.append(Q(subtype__in=facet_fields))

        if facet_languages := request.data.get("facet_languages"):
            facet_language_codes = set(map(lambda x: x.split("-")[0], facet_languages))
            iso639_1_codes = list(filter(lambda x: len(x) == 2, facet_language_codes))
            iso639_2_codes = list(filter(lambda x: len(x) == 3, facet_language_codes))
            # Always include indexables where no language is specified.
            # This will be cases where there it has neither iso639 field set.
            facet_language_filter = Q(language_iso639_1__isnull=True) & Q(
                language_iso639_2__isnull=True
            )
            if iso639_1_codes:
                facet_language_filter |= Q(language_iso639_1__in=iso639_1_codes)
            if iso639_2_codes:
                facet_language_filter |= Q(language_iso639_2__in=iso639_2_codes)
            facet_filters.append(facet_language_filter)

        indexables = (
            Indexable.objects.filter(*facet_filters)
            .values("type", "subtype", "group_id", "indexable_text")
            .annotate(n=Count("id", distinct=True))
            .order_by("type", "subtype", "group_id", "-n", "indexable_text")
        )

        return indexables

    def format_facet_data(self, request, indexables):
        grouped_facets = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        truncate_to = request.data.get("num_facets", 10)
        truncated_facets = defaultdict(lambda: defaultdict(dict))
        # Turn annotated list of results into a deeply nested dict
        for indexable in indexables:
            grouped_facets[indexable["type"]][indexable["subtype"]][
                indexable["indexable_text"]
            ] = indexable["n"]
        # Take the deeply nested dict and truncate the leaves of the tree to just N keys.
        for facet_type, facet_subtypes in grouped_facets.items():
            for k, v in facet_subtypes.items():
                truncated_facets[facet_type][k] = dict(
                    itertools.islice(v.items(), truncate_to)
                )
        return truncated_facets

    def get_facets(self, request, queryset):
        """ """
        indexable_data = self.get_facet_indexable_data(request, queryset)
        return self.format_facet_data(request, indexable_data)

    def get_search_data(self, request, queryset):
        """Create a dictionary of search related fields to include in the response."""
        return {"facets": self.get_facets(request, queryset)}

    def list(self, request, *args, **kwargs):
        """Duplicates the functionality of the list method
        from the `ListMethodMixin`, but includes fields
        created by the get_search_data in the response alongside
        results.
        """
        queryset = self.filter_queryset(self.get_queryset())

        search_data = self.get_search_data(request, queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            page_resp = self.get_paginated_response(serializer.data)
            page_resp.data.update(search_data)
            return page_resp

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data, **search_data})

    def create(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class BaseAPISearchViewSet(BaseSearchViewSet):
    """
    BaseClass for Search Service APIs.
    """

    pass


class BasePublicSearchViewSet(QueryParamDataMixin, BaseSearchViewSet):
    """
    BaseClass for Public Search Service APIs.
    Allows for querying via a GET request using query params, with the
    query_param_serializer_class being used to filter and transform data
    for parsing by the search parsers_classes.
    """

    permission_classes = [AllowAny]
    query_param_serializer_class = FacetedSearchQueryParamDataSerializer


class IndexableAPISearchViewSet(BaseAPISearchViewSet):
    queryset = Indexable.objects.all().distinct()
    parser_classes = [IndexableSearchParser]
    filter_backends = [AuthContextsFilter, GenericFilter]
    serializer_class = IndexableAPISearchSerializer


class SandboxedIndexableAPISearchViewSet(IndexableAPISearchViewSet):
    authentication_classes = [ContextsHeaderAuthentication]


class IndexablePublicSearchViewSet(BaseAPISearchViewSet):
    queryset = Indexable.objects.all().distinct()
    parser_classes = [IndexableSearchParser]
    filter_backends = [AuthContextsFilter, GenericFilter]
    serializer_class = IndexablePublicSearchSerializer


class JSONResourceAPISearchViewSet(BaseAPISearchViewSet):
    """ """

    queryset = JSONResource.objects.all().distinct()
    parser_classes = [ResourceSearchParser]
    lookup_field = "id"
    filter_backends = [
        AuthContextsFilter,
        ResourceFilter,
        FacetFilter,
        RankSnippetFilter,
    ]
    serializer_class = JSONResourceAPISearchSerializer


class SandboxedJSONResourceAPISearchViewSet(JSONResourceAPISearchViewSet):
    authentication_classes = [ContextsHeaderAuthentication]


class JSONResourcePublicSearchViewSet(BasePublicSearchViewSet):
    """ """

    queryset = JSONResource.objects.all().distinct()
    parser_classes = [ResourceSearchParser]
    lookup_field = "id"
    filter_backends = [
        AuthContextsFilter,
        ContextsFilter,
        ResourceFilter,
        FacetFilter,
        RankSnippetFilter,
    ]
    serializer_class = JSONResourcePublicSearchSerializer


class GenericFacetsViewSet(BasePublicSearchViewSet):
    """
    Simple read only view to return a list of facet fields
    """

    parser_classes = [SearchParser]
    filter_backends = [AuthContextsFilter, GenericFacetListFilter]
    serializer_class = IndexableAPISerializer

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
