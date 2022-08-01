"""
search_service/serializers/query_param.py - Serializer classes for transforming query parameters into parsable data.  
"""

import logging

from rest_framework import serializers

logger = logging.getLogger(__name__)


class FacetQueryParamSerializer(serializers.Serializer):
    """Parses a list of bar separated facet strings where
    the first component is the facet_type (e.g. metadata, tag)
    using serializer methods named get_{facet_type}_facet.

    e.g metadata|place|glasgow -> get_metadata_facet
        tag|81405 -> get_tag_facet
    """

    def to_representation(self, facets):
        indexable_facets = []
        for facet_string in facets:
            facet_components = facet_string.split("|")
            facet_type = facet_components[0]
            if facet_method := getattr(self, f"get_{facet_type}_facet", None):
                indexable_facets.append(facet_method(facet_components))
        return indexable_facets if indexable_facets else None


class StringQueryParamSerializer(serializers.Serializer):
    """Ensures a single string is returned from a query_param
    (default is to return as a list).
    """

    def to_representation(self, query_param):
        if query_param and isinstance(query_param, list):
            return query_param[0]
        else:
            return query_param


class MetadataFacetQueryParamSerializer(FacetQueryParamSerializer):
    """Provides a method for parsing metadata facets from a list
    of bar separated facet strings.
    """

    def get_metadata_facet(self, facet_components):
        facet_kwargs = ["type", "subtype", "value"]
        return {k: v for k, v in zip(facet_kwargs, facet_components)}


class FacetedSearchQueryParamDataSerializer(serializers.Serializer):
    """Serialises the fulltext and facet query params to populate
    the filter_data to be provided to the SearchParser.
    """

    fulltext = StringQueryParamSerializer(required=False)
    facets = MetadataFacetQueryParamSerializer(source="facet", required=False)
