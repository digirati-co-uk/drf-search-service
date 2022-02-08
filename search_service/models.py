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


class Indexables(UUIDModel, TimeStampedModel):
    """
    Model for storing indexable data per object

    id: autogenerated
    resource: e.g. manifest id, canvas id, etc (this is a foreign key)
    resource_id: this is just a string
    ? contexts: store here, or on the related resource (prob. resource)
    type: metadata, capture model, presentation_api, see_also
    language_iso639_2: e.g. eng, ara   ? store just this but use lookups to identify
    language_iso639_1: e.g. en, ar
    language_display: e.g English
    language_pg: postgres language
    indexable_int: indexable integer
    indexable_float: indexable float
    indexable_datetime: indexable date time
    indexable_json: indexable json
    indexable: concatenated/summarised content for indexing
    search_vector: search vector for the indexer to use
    original_content: textual content (as per original), if the original is JSON, this will be
        dumped/serialised JSON, rather than a JSON object

    N.B. gin index on search_vector for speed/performance

    https://www.loc.gov/standards/iso639-2/php/code_list.php
    """

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

    indexable = models.TextField()
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
                    "indexable", weight="A", config=self.language_pg
                )
            else:
                self.search_vector = SearchVector("indexable", weight="A")
            self.save(update_fields=["search_vector"])

    class Meta:
        # Add a postgres index for the search_vector
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
            HashIndex(fields=["indexable"]),
        ]


class Context(TimeStampedModel):
    """ "
    Context, i.e. the IIIF collection, manifest, Madoc site or project
    or any associated resource that is the context for a IIIF resource being indexed and
    searched against.

    id: Identifier (this is usually the Madoc ID but could be a IIIF @id)
    type: e.g. Site, Manifest, Collection, Project, etc. Not constrained.
    slug: a slugify'd version of the id for use in URL routing and URIs
    """

    id = models.CharField(
        max_length=512,
        primary_key=True,
        editable=True,
        verbose_name=_("Identifier (Context)"),
    )
    type = models.CharField(max_length=30)
    slug = AutoSlugField(populate_from="id", max_length=512)


class BaseSearchResource(UUIDModel, TimeStampedModel): 
    
    class Meta: 
        abstract = True
        ordering = ['-modified']

class JSONResource(BaseSearchResource): 
    """ An example resource for indexing. 
        """
    indexables = GenericRelation(
        Indexables,
        content_type_field="resource_content_type",
        object_id_field="resource_id",
        related_query_name="json_resources", 
    )
    label = models.CharField(max_length=50)
    data = models.JSONField(blank=True)


