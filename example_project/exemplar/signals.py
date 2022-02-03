import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from search_service.tasks import (
        BaseSearchServiceIndexingTask, 
        )

from .models import ExemplarResource
from .serializers import ExemplarResourceToIndexablesSerializer

logger = logging.getLogger(__name__)

class ExemplarIndexingTask(BaseSearchServiceIndexingTask): 
    model = ExemplarResource
    serializer_class = ExemplarResourceToIndexablesSerializer



@receiver(post_save, sender=ExemplarResource)
def index_exemplar_resource(sender, instance, **kwargs):
    logger.info(instance)
    task = ExemplarIndexingTask(instance.id)
    task.run()

