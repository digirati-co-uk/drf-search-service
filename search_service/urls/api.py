"""
search_service/urls/api.py - DefaultRouter registration of API Viewsets.  
"""

from rest_framework import routers

from ..views import (
    JSONResourceAPIViewSet,
    IndexableAPIViewSet,
    ResourceRelationshipAPIViewSet,
    ContentTypeAPIViewSet,
    IndexableAPISearchViewSet, 
    JSONResourceAPISearchViewSet, 
)

app_name = "search_service"

router = routers.DefaultRouter()
router.register("indexable", IndexableAPIViewSet)
router.register("resource_relationship", ResourceRelationshipAPIViewSet)
router.register("content_type", ContentTypeAPIViewSet)
router.register("json_resource", JSONResourceAPIViewSet)
router.register("indexable_search", IndexableAPISearchViewSet)
router.register("json_resource_search", JSONResourceAPISearchViewSet)

urlpatterns = router.urls
