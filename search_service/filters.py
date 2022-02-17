import logging

from django.contrib.postgres.search import SearchRank
from django.db.models import F
from django.db.models import Max
from django.db.models import OuterRef, Subquery
from django.db.models import Q, Value, FloatField
from rest_framework.filters import BaseFilterBackend
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline
from django.db.models.functions import Concat
from django.db.models import F, Value, CharField
from .models import Indexable, BaseSearchResource, JSONResource, ResourceRelationship

logger = logging.getLogger(__name__)


class FacetListFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """

        if request.data.get("prefilter_kwargs", None):
            # Just check if this thing is all nested Q() objects
            if all([type(k) == Q for k in request.data["prefilter_kwargs"]]):
                # This is a chaining operation
                for f in request.data["prefilter_kwargs"]:
                    queryset = queryset.filter(*(f,))
        return queryset


class GenericFacetListFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """

        if request.data.get("facet_list_filters", None):
            # Just check if this thing is all nested Q() objects
            if all([type(k) == Q for k in request.data["facet_list_filters"]]):
                # This is a chaining operation
                for f in request.data["facet_list_filters"]:
                    queryset = queryset.filter(*(f,))
        return queryset


class FacetListFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """

        if request.data.get("prefilter_kwargs", None):
            # Just check if this thing is all nested Q() objects
            if all([type(k) == Q for k in request.data["prefilter_kwargs"]]):
                # This is a chaining operation
                for f in request.data["prefilter_kwargs"]:
                    queryset = queryset.filter(*(f,))
        return queryset


class GenericFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset. Expects a Django Q object
        to apply the filtering and an optional headline_query
        which is a SearchQuery object that can be used by
        SearchRank and SearchHeadline to annotate the results with ranking
        and with snippets.
        """
        if (_filter := request.data.get("filter", None)) is not None:
            if type(_filter) == Q:
                queryset = queryset.filter(_filter)
                # This only applies if there is a fulltext query we can use to rank
                # and generate snippets
                if (
                    search_query := request.data.get("headline_query", None)
                ) is not None:
                    queryset = (
                        queryset.annotate(
                            rank=SearchRank(
                                F("search_vector"), search_query, cover_density=True
                            ),
                            snippet=Concat(
                                Value("'"),
                                SearchHeadline(
                                    "original_content",
                                    search_query,
                                    max_words=50,
                                    min_words=25,
                                    max_fragments=3,
                                ),
                                output_field=CharField(),
                            ),
                            fullsnip=SearchHeadline(
                                "indexable_text",
                                search_query,
                                start_sel="<b>",
                                stop_sel="</b>",
                                highlight_all=True,
                            ),
                        )
                        .filter(_filter, rank__gt=0.0)
                        .order_by("-rank")
                    )
        return queryset


class ResourceFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset. Expects a Django Q object
        to apply the filtering.
        """
        if (_filter := request.data.get("filter_query", None)) is not None and type(
            _filter
        ) == Q:
            queryset = queryset.filter(_filter)
        return queryset.prefetch_related("relationship_sources")


class FacetFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset. Expects a list of Django Q objects.
        """
        facetable = queryset
        filter_facetable_resources = request.data.get("facet_on", None)
        if (
            filter_facetable_resources and queryset
        ):  # Facet on something other than the original queryset
            facetable = (
                queryset.first()
                .__class__.objects.all()
                .filter(
                    filter_facetable_resources,
                    pk__in=queryset.values("relationship_sources__target_id"),
                )
            )
        if (
            facet_filter := request.data.get("facet_filters", None)
        ) is not None and all([type(f) == Q for f in facet_filter]):
            for f in facet_filter:
                facetable = facetable.filter(*(f,))
        if filter_facetable_resources:
            return queryset.filter(
                pk__in=facetable.values("relationship_targets__source_id")
            )
        else:
            return facetable


class RankSnippetFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset. Expects an optional headline_query
        which is a SearchQuery object that can be used by
        SearchRank and SearchHeadline to annotate the results with ranking
        and with snippets.
        """
        if (
            search_query := request.data.get("headline_query", None)
        ) is not None and isinstance(search_query, SearchQuery):
            if queryset:
                # Create a subquery to produce the matching snippets and ranks
                # on the Indexables
                matches = (
                    Indexable.objects.filter(resource_id=OuterRef("pk"))
                    .annotate(
                        highlight=Concat(
                            Value("'"),
                            SearchHeadline(
                                "indexable_text",
                                search_query,
                                max_words=50,
                                min_words=25,
                                max_fragments=3,
                            ),
                            output_field=CharField(),
                        )
                    )
                    .annotate(
                        rank=SearchRank(
                            F("search_vector"),
                            search_query,
                            cover_density=True,
                        )
                    )
                    .order_by("-rank")
                )
                return (
                    queryset.annotate(  # this will effectively be Max(rank) as we are ordering by descending rank
                        rank=Subquery(matches.values("rank")[:1]),
                        snippet=Subquery(matches.values("highlight")[:1]),
                    )
                    .filter(rank__gt=0.0)
                    .order_by("-rank")
                    .distinct()
                )
        return queryset.distinct()
