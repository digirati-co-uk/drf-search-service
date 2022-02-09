from django.urls import path, include
from rest_framework import routers

from .views import (
    JSONResourceViewSet,
    IndexableViewSet,
    JSONResourceSearchViewSet,
    GenericSearchBaseViewSet,
)

app_name = "search_service"

router = routers.DefaultRouter(trailing_slash=False)
router.register("json_resource", JSONResourceViewSet, basename="iiif")
router.register("indexables", IndexableViewSet, basename="indexables")
router.register("generic_search", GenericSearchBaseViewSet, basename="generic_search")
router.register("json_search", JSONResourceSearchViewSet, basename="json_search")

urlpatterns = router.urls
