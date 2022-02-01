import logging

from rest_framework import viewsets

from .models import (
        ExemplarResource, 
        )

from .serializers import (
        ExemplarResourceSerializer, 
        )


logger = logging.getLogger(__name__)

class ExemplarResourceViewSet(viewsets.ModelViewSet):
    queryset = ExemplarResource.objects.order_by("-modified")
    serializer_class = ExemplarResourceSerializer
    lookup_field = "id"
