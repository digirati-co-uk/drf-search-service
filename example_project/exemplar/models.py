import logging
import uuid
from django.contrib.gis.db import models
from model_utils.models import (
        TimeStampedModel, 
        UUIDModel
        )

logger = logging.getLogger(__name__)

class ExemplarResource(UUIDModel, TimeStampedModel):
    label = models.CharField(max_length=50)
    data = models.JSONField(blank=True)
