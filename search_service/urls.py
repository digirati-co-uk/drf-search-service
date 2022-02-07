from django.urls import path, include
from rest_framework import routers

from .views import (
    IIIFViewSet,
    ContextViewSet,
    IndexablesViewSet,
    CaptureModelViewSet,
    IIIFSearch,
    Facets,
    Autocomplete,
)

app_name = "search_service"

router = routers.DefaultRouter(trailing_slash=False)
router.register("capture_model", CaptureModelViewSet, basename="capture_model")
router.register("iiif", IIIFViewSet, basename="iiif")
router.register("indexables", IndexablesViewSet, basename="indexables")
router.register("context", ContextViewSet, basename="context")
router.register("search", IIIFSearch, basename="search")
router.register("facets", Facets, basename="facets")
router.register("autocomplete", Autocomplete, basename="autocomplete")

urlpatterns = router.urls
