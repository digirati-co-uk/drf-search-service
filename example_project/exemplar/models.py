import logging
import uuid
from django.contrib.gis.db import models
from django.contrib.contenttypes.fields import GenericRelation
from model_utils.models import TimeStampedModel, UUIDModel

from search_service.models import (
    Indexables,
)

logger = logging.getLogger(__name__)


class ExemplarResource(UUIDModel, TimeStampedModel):
    indexables = GenericRelation(
        Indexables,
        content_type_field="resource_content_type",
        object_id_field="resource_id",

        related_query_name="exemplar_resources", # resource specific. 
    )
    label = models.CharField(max_length=50)
    data = models.JSONField(blank=True)
