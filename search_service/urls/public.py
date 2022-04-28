"""
search_service/urls/public.py SimpleRouter registration of Public Viewsets.  
"""
from rest_framework import routers

from ..views import (
    JSONResourceSearchViewSet,
    GenericSearchBaseViewSet,
)

app_name = "search_service"

router = routers.SimpleRouter(trailing_slash = True)
router.register("generic_search", GenericSearchBaseViewSet, basename="generic_search")
router.register("json_search", JSONResourceSearchViewSet, basename="json_search")

urlpatterns = router.urls
