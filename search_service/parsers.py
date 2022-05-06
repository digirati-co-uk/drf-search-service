import codecs
import json
from functools import reduce
from operator import or_, and_
import pytz
from dateutil import parser
import logging
import unicodedata

# Django imports
from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.db.models import Q
from django.utils.translation import get_language


# DRF Imports
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


from .models import BaseSearchResource
from .settings import search_service_settings


default_lang = get_language()

logger = logging.getLogger(__name__)


def date_query_value(q_key, value):
    """
    To aid in the faceting, if you get a query type that is date, return a datetime parsed using dateutil,
    otherwise, just return the thing that came in
    """
    if "date" in q_key:
        try:
            parsed_date = parser.parse(value)
            if (
                parsed_date.tzinfo is None
                or parsed_date.tzinfo.utcoffset(parsed_date) is None
            ):
                query_date = parsed_date.replace(tzinfo=pytz.utc)
            else:
                query_date = parsed_date
        except ValueError:
            query_date = None
        if query_date:
            return query_date
        else:
            return value
    return value


def facet_operator(q_key, field_lookup):
    """
    sorted_facet_query.get('field_lookup', 'iexact')
    """
    if q_key in ["type", "subtype", "group_id"]:
        return "iexact"
    elif q_key in ["value"]:
        if field_lookup in [
            "exact",
            "iexact",
            "icontains",
            "contains",
            "in",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
        ]:
            return field_lookup
        else:
            return "iexact"
    elif q_key in ["indexable_int", "indexable_float"]:
        if field_lookup in ["exact", "gt", "gte", "lt", "lte"]:
            return field_lookup
        else:
            return "exact"
    elif q_key in ["indexable_date_range_start", "indexable_date_range_year"]:
        if field_lookup in [
            "day",
            "month",
            "year",
            "iso_year",
            "gt",
            "gte",
            "lt",
            "lte",
            "exact",
        ]:
            return field_lookup
        else:
            return "exact"
    else:
        return "iexact"


def parse_facets(facet_queries, prefix_q=""):
    """
    Parse the facet component of a search request into a set of reduced Q filters.
    """
    if facet_queries:
        postfilter_q = []
        # Generate a list of keys concatenated from type and subtype
        # These should be "OR"d together later.
        # e.g.
        # {"metadata|author": []}
        sorted_facets = {
            "|".join([f.get("type", ""), f.get("subtype", "")]): []
            for f in facet_queries
        }
        # Copy the query into that lookup so we can get queries against the same
        # type/subtype
        # e.g.
        # {"metadata|author": ["John Smith", "Mary Jones"]}
        for f in facet_queries:
            sorted_facets["|".join([f.get("type", ""), f.get("subtype", "")])].append(f)
        for sorted_facet_key, sorted_facet_queries in sorted_facets.items():
            # For each combination of type/subtype
            # 1. Concatenate all of the queries into an AND
            # e.g. "type" = "metadata" AND "subtype" = "author" AND
            # "indexables" = "John Smith"
            # 2. Concatenate all of thes einto an OR
            # so that you get something with the intent of AUTHOR = (A or B)
            postfilter_q.append(
                reduce(  # All of the queries with the same field are OR'd together
                    or_,
                    [
                        reduce(  # All of the fields within a single facet query are
                            # AND'd together
                            and_,
                            (
                                Q(  # Iterate the keys in the facet dict to generate the Q()
                                    **{
                                        f"{prefix_q}"
                                        f"{(lambda k: 'indexable_text' if k == 'value' else k)(k)}__"
                                        f"{facet_operator(k, sorted_facet_query.get('field_lookup', 'iexact'))}": date_query_value(
                                            q_key=k, value=v
                                        )
                                    }  # You can pass in something other than iexact
                                    # using the field_lookup key
                                )
                                for k, v in sorted_facet_query.items()
                                if k
                                in [
                                    "type",
                                    "subtype",
                                    "group_id",
                                    "indexable_text",
                                    "value",
                                    "indexable_int",
                                    "ndexable_float",
                                    "indexable_date_range_start",
                                    "indexable_date_range_end",
                                ]  # These are the fields to query
                            ),
                        )
                        for sorted_facet_query in sorted_facet_queries
                    ],
                )
            )
        return postfilter_q
    return


def is_latin(text):
    """
    Function to evaluate whether a piece of text is all Latin characters, numbers or punctuation.

    Can be used to test whether a search phrase is suitable for parsing as a fulltext query, or whether it
    should be treated as an "icontains" or similarly language independent query filter.
    """
    return all(
        [
            (
                "LATIN" in unicodedata.name(x)
                or unicodedata.category(x).startswith("P")
                or unicodedata.category(x).startswith("N")
                or unicodedata.category(x).startswith("Z")
            )
            for x in text
        ]
    )


class SearchParser(JSONParser):
    """
    Generic search parser that makes no assumptions about the shape of the resource
    that is linked to the Indexable.
    """

    numerical_operators = [
        "exact",
        "gt",
        "lt",
        "gte",
        "lte",
    ]
    default_search_language = None
    default_search_type = search_service_settings.DEFAULT_SEARCH_TYPE
    default_facet_types = search_service_settings.DEFAULT_FACET_TYPES
    q_prefix = ""

    def float_filter_kwargs(self, request_data, key="float", default_value=None):
        f_kwargs = {}
        if query := request_data.get(key, default_value):
            if (value := query.get("value")) and (
                operator := query.get("operator", "exact")
            ) in self.numerical_operators:
                f_kwargs[f"{self.q_prefix}indexable_float__{operator}"] = value
        return f_kwargs

    def integer_filter_kwargs(self, request_data, key="integer", default_value=None):
        f_kwargs = {}
        if query := request_data.get(key, default_value):
            if (value := query.get("value")) and (
                operator := query.get("operator", "exact")
            ) in self.numerical_operators:
                f_kwargs[f"{self.q_prefix}indexable_integer__{operator}"] = value
        return f_kwargs

    def date_filter_kwargs(self, request_data, key="date_exact", default_value=None):
        date_types = {
            "date_start": [f"{self.q_prefix}indexable_date_range_end__gte"],
            "date_end": [f"{self.q_prefix}indexable_date_range_start__lte"],
            "date_exact": [
                f"{self.q_prefix}indexable_date_range_start",
                f"{self.q_prefix}indexable_date_range_end",
            ],
        }
        f_kwargs = {}
        if query := request_data.get(key, default_value):
            if value := query.get("value"):
                try:
                    parsed_date = parser.parse(value)
                    if (
                        parsed_date.tzinfo is None
                        or parsed_date.tzinfo.utcoffset(parsed_date) is None
                    ):
                        query_date = parsed_date.replace(tzinfo=pytz.utc)
                    else:
                        query_date = parsed_date

                    f_kwargs = {x: query_date for x in date_types[key]}
                except ValueError:
                    pass
        return f_kwargs

    def indexable_field_filter_kwargs(self, request_data):
        indexable_fields = [
            "type",
            "subtype",
            "language_iso639_2",
            "language_iso639_1",
            "language_display",
            "language_pg",
            "group_id",
        ]
        return {
            f"{self.q_prefix}{indexable_field}__iexact": value
            for indexable_field in indexable_fields
            if (value := request_data.get(indexable_field))
        }

    def parse_filter_kwargs(self, request_data):
        return {
            **self.float_filter_kwargs(request_data),
            **self.integer_filter_kwargs(request_data),
            **self.date_filter_kwargs(request_data, key="date_start"),
            **self.date_filter_kwargs(request_data, key="date_end"),
            **self.date_filter_kwargs(request_data, key="date_exact"),
            **self.integer_filter_kwargs(request_data),
        }

    def parse_search_query(self, request_data):
        non_vector_search = [Q()]
        filter_kwargs = {}
        search_language = request_data.get(
            "search_language", self.default_search_language
        )
        search_type = request_data.get("search_type", self.default_search_type)
        non_latin_fulltext = request_data.get(
            "non_latin_fulltext", search_service_settings.NONLATIN_FULLTEXT
        )
        search_multiple_fields = request_data.get(
            "search_multiple_fields", search_service_settings.SEARCH_MULTIPLE_FIELDS
        )

        if search_string := request_data.get("fulltext", None):
            if (
                non_latin_fulltext or is_latin(search_string)
            ) and not search_multiple_fields:
                logger.debug(f"Search string {search_string}")
                if search_language:
                    filter_kwargs = {
                        f"{self.q_prefix}search_vector": SearchQuery(
                            search_string,
                            config=search_language,
                            search_type=search_type,
                        )
                    }
                else:
                    filter_kwargs = {
                        f"{self.q_prefix}search_vector": SearchQuery(
                            search_string, search_type=search_type
                        )
                    }
            else:
                # Should be an independent `get_non_vector_search` method. 
                non_vector_search = [
                    reduce(
                        and_,
                        [
                            Q(
                                **{
                                    f"{self.q_prefix}indexable_text__icontains": split_search
                                }
                            )
                            for split_search in search_string.split()
                        ],
                    )
                ]
        return filter_kwargs, non_vector_search

    def get_headline_query(self, request_data):
        headline_query = None
        search_type = request_data.get("search_type", self.default_search_type)
        if search_string := request_data.get("fulltext", None):
            if search_language := request_data.get("search_language", None):
                headline_query = SearchQuery(
                    search_string, config=search_language, search_type=search_type
                )
            else:
                headline_query = SearchQuery(search_string, search_type=search_type)

        return headline_query

    def get_facet_on_query(self, request_data):
        facet_on_q = Q()
        if facet_on := request_data.get("facet_on", None):
            facet_on_q = Q(**facet_on)
        return facet_on_q

    def get_facet_filters(self, request_data):
        facet_filters = None
        if facet_queries := request_data.get("facets", None):
            facet_filters = parse_facets(
                facet_queries=facet_queries, prefix_q=self.q_prefix
            )

        return facet_filters

    def get_filter_query(self, request_data):
        non_vector_search = [Q()]
        main_filters = [Q()]
        filter_kwargs = self.parse_filter_kwargs(request_data)
        # Fulltext search
        search_query_filter_kwargs, non_vector_search = self.parse_search_query(
            request_data
        )
        filter_kwargs = {**filter_kwargs, **search_query_filter_kwargs}
        resource_filter_q = [Q()]
        if filter_kwargs:
            main_filters = [
                reduce(
                    and_,
                    [Q(**{key: value}) for key, value in filter_kwargs.items()],
                )
            ]

        # Construct the primary Q object by 'AND'-ing everything together
        filter_q = reduce(and_, resource_filter_q + non_vector_search + main_filters)
        return filter_q

    def get_resource_filters(self, request_data):
        """
        Parse the filters that apply to the resource class associated with this queryset
        parser validates that these are all dicts with the right keys but does not
        construct the Q object as that requires access to the queryset app label
        """
        resource_filter_queries = []
        resource_filters = request_data.get("resource_filters", None)
        if (
            resource_filters
            and isinstance(resource_filters, list)
            and all([isinstance(x, dict) for x in resource_filters])
        ):
            resource_filter_queries += [
                d
                for d in resource_filters
                if all(
                    [x in d for x in ["resource_class", "field", "operator", "value"]]
                )
            ]
        return resource_filter_queries

    def parse_data(self, request_data): 
        logger.debug(f"Parsing filter data from: ({request_data})")
        filter_data = {
            "filter_query": self.get_filter_query(
                request_data
            ),  # fulltext plus indexable properties
            "resource_filters": self.get_resource_filters(request_data),
            "headline_query": self.get_headline_query(request_data),  # fulltext
            "facet_filters": self.get_facet_filters(request_data),  # facets
            "facet_on": self.get_facet_on_query(
                request_data
            ),  # query that identifies the queryset to facet over
            "facet_types": request_data.get("facet_types", self.default_facet_types), 
            "query_prefix": self.q_prefix,
        }

        logger.debug(f"Parsed search filter data: ({filter_data})")
        return filter_data

    def parse(self, stream, media_type=None, parser_context={}):
        request_data = super().parse(stream, media_type, parser_context)
        return self.parse_data(request_data)

class IndexableSearchParser(SearchParser):
    """
    Generic search parser that makes no assumptions about the shape of the resource
    that is linked to the Indexable.
    """
    q_prefix = ""

class ResourceSearchParser(SearchParser):
    """
    Generic search parser that makes no assumptions about the shape of the resource
    that is linked to the Indexable.
    """
    q_prefix = "indexables__"
