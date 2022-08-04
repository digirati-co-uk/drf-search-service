"""
search_service/serializers/api.py - Serializer classes for API views
"""

import logging

from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from ..models import (
    Namespace,
    Indexable,
    ResourceRelationship,
    BaseSearchResource,
    JSONResource,
)
from ..signals import (
    ready_for_indexing,
)

from .fields import (
    NamespacesField,
)


logger = logging.getLogger(__name__)


class ContentTypeAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = [
            "id",
            "app_label",
            "model",
        ]


class NamespaceAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = Namespace
        fields = [
            "id",
            "created",
            "modified",
            "urn",
        ]


class AuthNamespacesValidationMixin: 

    def validate(self, data):
        """Used to ensure the presence of any required namespaces
        set by an authentication_class on the serializer context.
        """
        namespaces = []
        current_namespaces = data.get("namespaces", [])
        if request := self.context.get("request"):
            if request.auth and (auth_namespaces := request.auth.get("namespaces")):
                namespaces += auth_namespaces
        additional_namespaces = NamespacesField(many=True, slug_field="urn").to_internal_value(namespaces)
        data["namespaces"] = current_namespaces + additional_namespaces
        return data



class BaseResourceAPISerializer(AuthNamespacesValidationMixin, serializers.ModelSerializer):
    namespaces = NamespacesField(many=True, slug_field="urn", required=False)

    def signal_completed(self, instance):
        logger.debug(instance.__class__)
        ready_for_indexing.send(sender=instance.__class__, instance=instance)

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.signal_completed(instance)
        return instance

    def update(self, validated_data):
        instance = super().update(validated_data)
        self.signal_completed(instance)
        return instance


class JSONResourceAPISerializer(BaseResourceAPISerializer):
    class Meta:
        model = JSONResource
        fields = [
            "id",
            "created",
            "modified",
            "namespaces",
            "label",
            "data",
        ]


class ResourceRelationshipAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceRelationship
        fields = [
            "id",
            "created",
            "modified",
            "source_id",
            "source_content_type",
            "type",
            "target_id",
            "target_content_type",
        ]


class IndexableAPISerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Indexable, i.e. the indexed objects that are used to
    drive search and which are associated with a IIIF resource
    """

    namespaces = NamespacesField(many=True, slug_field="urn", required=False)

    class Meta:
        model = Indexable
        fields = [
            "url",
            "resource_id",
            "content_id",
            "original_content",
            "namespaces",
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
                "view_name": "api:search_service:indexable-detail",
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
        return super(IndexableAPISerializer, self).create(validated_data)
