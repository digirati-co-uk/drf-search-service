import logging

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import GinIndex, HashIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models.functions import Upper

# from .langbase import INTERNET_LANGUAGES
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from model_utils.models import TimeStampedModel, UUIDModel

logger = logging.getLogger(__name__)


class Indexable(UUIDModel, TimeStampedModel):
    """ """

    resource_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    resource_id = models.UUIDField()
    resource = GenericForeignKey("resource_content_type", "resource_id")

    type = models.CharField(max_length=64)
    subtype = models.CharField(max_length=256)
    group_id = models.CharField(
        max_length=512,
        verbose_name=_("Identifier for grouping indexables, e.g. by vocab identifier"),
        blank=True,
        null=True,
    )

    content_id = models.CharField(
        max_length=512,
        verbose_name=_("Identifier (URL/URI/URN) for the content, if it has one"),
        blank=True,
        null=True,
    )

    indexable_text = models.TextField()
    indexable_date_range_start = models.DateTimeField(blank=True, null=True)
    indexable_date_range_end = models.DateTimeField(blank=True, null=True)
    indexable_int = models.IntegerField(blank=True, null=True)
    indexable_json = models.JSONField(blank=True, null=True)
    indexable_float = models.FloatField(blank=True, null=True)
    original_content = models.TextField()
    search_vector = SearchVectorField(blank=True, null=True)
    language_iso639_2 = models.CharField(max_length=3, blank=True, null=True)
    language_iso639_1 = models.CharField(max_length=2, blank=True, null=True)
    language_display = models.CharField(max_length=64, blank=True, null=True)
    language_pg = models.CharField(max_length=64, blank=True, null=True)
    selector = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if (
            "update_fields" not in kwargs
            or "search_vector" not in kwargs["update_fields"]
        ):
            if self.language_pg:
                self.search_vector = SearchVector(
                    "indexable_text", weight="A", config=self.language_pg
                )
            else:
                self.search_vector = SearchVector("indexable_text", weight="A")
            self.save(update_fields=["search_vector"])

    class Meta:
        # Add a postgres index for the search_vector
        ordering = ["-modified"]
        indexes = [
            GinIndex(fields=["search_vector"]),
            models.Index(fields=["content_id"]),
            models.Index(fields=["resource_id"]),
            models.Index(
                fields=["language_iso639_2", "language_iso639_1", "language_display"]
            ),
            models.Index(fields=["type"]),
            models.Index(fields=["subtype"]),
            models.Index(fields=["group_id"]),
            models.Index(fields=["type", "subtype"]),
            models.Index(fields=["type", "subtype", "group_id"]),
            models.Index(Upper("type"), name="uppercase_type"),
            models.Index(Upper("subtype"), name="uppercase_subtype"),
            models.Index(
                Upper("type"), Upper("subtype"), name="uppercase_type_subtype"
            ),
            HashIndex(fields=["indexable_text"]),
        ]


class ResourceRelationship(UUIDModel, TimeStampedModel):
    """ Model-agnostic relationship between resources. 
        """
    source_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="%(class)s_sources"
    )
    source_id = models.UUIDField()
    source = GenericForeignKey("source_content_type", "source_id")
    target_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="%(class)s_targets"
    )
    target_id = models.UUIDField()
    target = GenericForeignKey("target_content_type", "target_id")
    type = models.CharField(max_length=100)

    class Meta:
        ordering = ["-modified"]


class BaseSearchResource(UUIDModel, TimeStampedModel):
    indexables = GenericRelation(
        Indexable,
        content_type_field="resource_content_type",
        object_id_field="resource_id",
        related_query_name="%(class)s",
    )
    relationship_sources = GenericRelation(
        ResourceRelationship,
        content_type_field="source_content_type",
        object_id_field="source_id",
        related_query_name="%(class)s_sources",
    )
    relationship_targets = GenericRelation(
        ResourceRelationship,
        content_type_field="target_content_type",
        object_id_field="target_id",
        related_query_name="%(class)s_targets",
    )

    class Meta:
        abstract = True
        ordering = ["-modified"]


class JSONResource(BaseSearchResource):
    """An example resource for indexing."""

    label = models.CharField(max_length=50)
    data = models.JSONField(blank=True)
