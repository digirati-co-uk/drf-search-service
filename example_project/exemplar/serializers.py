import logging
from rest_framework import serializers

from .models import (
        ExemplarResource, 
        )

logger = logging.getLogger(__name__)

class ExemplarResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExemplarResource
        fields = [
            "id",
            "created",
            "modified",
            "label",
            "data",
        ]
