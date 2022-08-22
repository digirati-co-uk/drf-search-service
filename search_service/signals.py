import logging

from django.dispatch import (
    Signal,
    receiver,
)

from .models import JSONResource
from .tasks import JSONResourceIndexingTask

ready_for_indexing = Signal()

logger = logging.getLogger(__name__)


@receiver(ready_for_indexing, sender=JSONResource)
def index_json_resource(sender, instance, **kwargs):
    logger.info(f"Running indexing task for: ({instance})")
    task = JSONResourceIndexingTask(instance.id)
    task.run()
