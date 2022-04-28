"""
search_service/urls/api.py - DefaultRouter registration of API Viewsets.  
"""

from rest_framework import routers

from ..views import (
    JSONResourceAPIViewSet,
    IndexableAPIViewSet,
    ResourceRelationshipAPIViewSet,
    ContentTypeAPIViewSet,
)

app_name = "search_service"

router = routers.DefaultRouter()
router.register("json_resource", JSONResourceAPIViewSet)
router.register("indexable", IndexableAPIViewSet)
router.register("resource_relationship", ResourceRelationshipAPIViewSet)
router.register("content_type", ContentTypeAPIViewSet)

urlpatterns = router.urls
