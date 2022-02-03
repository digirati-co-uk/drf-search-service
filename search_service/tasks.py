import logging

from .serializers import (
    IndexablesCreateUpdateSerializer,
)

logger = logging.getLogger(__name__)


class BaseSearchServiceIndexingTask(object):
    model = None
    serializer_class = None

    def __init__(self, object_id):
        self.object_id = object_id

    def get_object(self):
        try:
            logger.debug(
                f"Fetching object for indexing: ({self.model=}, {self.object_id=})"
            )
            return self.model.objects.get(id=self.object_id)
        except model.DoesNotExist as e:
            logger.error(
                f"Object not present for indexing: ({self.model=}, {self.object_id=})"
            )
            raise e

    def get_serializer(self, *args, **kwargs):
        logger.debug(
            f"Generating indexable data from object with serializer: ({self.model=}, {self.serializer_class=})"
        )
        return self.serializer_class(*args, **kwargs)

    def delete_existing_indexables(self, instance):
        logger.debug(
            f"Deleting existing indexables for object: ({self.model=}, {self.object_id=})"
        )
        instance.indexables.all().delete()

    def run(self):
        instance = self.get_object()
        instance_indexables = self.get_serializer(instance)
        indexables_serializer = IndexablesCreateUpdateSerializer(
            data=instance_indexables.data, many=True
        )
        if indexables_serializer.is_valid():
            logger.info(indexables_serializer.validated_data)
            indexables_serializer.save()
            return indexables_serializer.data
        else:
            logger.error("Failed to create indexables")
            logger.info(indexables_serializer.errors)
            return indexables_serializer.errors
