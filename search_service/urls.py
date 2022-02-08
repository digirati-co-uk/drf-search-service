from django.urls import path, include
from rest_framework import routers

from .views import (
    JSONResourceViewSet,
    IndexablesViewSet,
    JSONResourceSearch,
    GenericSearchBaseClass
)

app_name = "search_service"

router = routers.DefaultRouter(trailing_slash=False)
router.register("json_resource", JSONResourceViewSet, basename="iiif")
router.register("indexables", IndexablesViewSet, basename="indexables")
# router.register("json_search", JSONResourceSearch, basename="json_search")


urlpatterns = router.urls

urlpatterns += [
    path("json_search", JSONResourceSearch.as_view({"get": "list", "post": "list"}),
         name="search_service.api.json_search"),
    path("generic_search", GenericSearchBaseClass.as_view({"get": "list", "post": "list"}),
         name="search_service.api.generic_search")
]
