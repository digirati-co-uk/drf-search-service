"""
search_service/urls/public.py SimpleRouter registration of Public Viewsets.  
"""
from rest_framework import routers

from ..views import (
    IndexablePublicSearchViewSet, 
    JSONResourcePublicSearchViewSet, 
)

app_name = "search_service"

router = routers.SimpleRouter(trailing_slash = True)
router.register("indexable_search", IndexablePublicSearchViewSet, basename="indexable_search")
router.register("json_resource_search", JSONResourcePublicSearchViewSet, basename="json_search")

urlpatterns = router.urls
