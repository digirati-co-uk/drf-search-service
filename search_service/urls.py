from django.urls import path, include
from rest_framework import routers

from .views import (
    JSONResourceViewSet,
    IndexablesViewSet,
    JSONResourceSearchViewSet,
    GenericSearchBaseViewSet,
    GenericFacetsViewSet,
)

app_name = "search_service"

router = routers.DefaultRouter(trailing_slash=False)
router.register("json_resource", JSONResourceViewSet, basename="iiif")
router.register("indexables", IndexablesViewSet, basename="indexables")
router.register("generic_search", GenericSearchBaseViewSet, basename="generic_search")
router.register("generic_facets", GenericFacetsViewSet, basename="generic_facets")
router.register("json_search", JSONResourceSearchViewSet, basename="json_search")

urlpatterns = router.urls
