from django.urls import path, include
from rest_framework import routers

from .views import (
    JSONResourceViewSet,
    ContextViewSet,
    IndexablesViewSet,
    IIIFSearch,
    Facets,
    Autocomplete,
)

app_name = "search_service"

router = routers.DefaultRouter(trailing_slash=False)
router.register("json_resource", JSONResourceViewSet, basename="iiif")
router.register("indexables", IndexablesViewSet, basename="indexables")
router.register("context", ContextViewSet, basename="context")
router.register("search", IIIFSearch, basename="search")
router.register("facets", Facets, basename="facets")
router.register("autocomplete", Autocomplete, basename="autocomplete")

urlpatterns = router.urls
