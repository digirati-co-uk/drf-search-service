import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import JSONResource
from .tasks import JSONResourceIndexingTask


logger = logging.getLogger(__name__)


@receiver(post_save, sender=JSONResource)
def index_json_resource(sender, instance, **kwargs):
    logger.info(instance)
    task = JSONResourceIndexingTask(instance.id)
    task.run()
