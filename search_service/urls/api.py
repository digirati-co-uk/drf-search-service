"""
search_service/urls/api.py - DefaultRouter registration of API Viewsets.  
"""

from rest_framework import routers

from ..views import (
    JSONResourceAPIViewSet,
    NamespaceAPIViewSet,
    IndexableAPIViewSet,
    ResourceRelationshipAPIViewSet,
    ContentTypeAPIViewSet,
    IndexableAPISearchViewSet,
    JSONResourceAPISearchViewSet,
    # Namespaced viewsets
    NamespacedJSONResourceAPIViewSet,
    NamespacedIndexableAPIViewSet,
    NamespacedIndexableAPISearchViewSet,
    NamespacedJSONResourceAPISearchViewSet,
)

app_name = "search_service"

router = routers.DefaultRouter()
router.register("indexable", IndexableAPIViewSet)
router.register("namespace", NamespaceAPIViewSet)
router.register("resource_relationship", ResourceRelationshipAPIViewSet)
router.register("content_type", ContentTypeAPIViewSet)
router.register("json_resource", JSONResourceAPIViewSet)
router.register("indexable_search", IndexableAPISearchViewSet)
router.register("json_resource_search", JSONResourceAPISearchViewSet)

# Only included in the example_project for testing
# Authentication classes should be set globally, 
# or directly on inheriting ViewSets (as below) if namespacing is required
namespaced_router = routers.DefaultRouter()
namespaced_router.register(
    "indexable", NamespacedIndexableAPIViewSet, basename="namespaced_indexable"
)
namespaced_router.register(
    "json_resource",
    NamespacedJSONResourceAPIViewSet,
    basename="namespaced_jsonresource",
)
namespaced_router.register(
    "indexable_search",
    NamespacedIndexableAPISearchViewSet,
    basename="namespaced_indexable_search",
)
namespaced_router.register(
    "json_resource_search",
    NamespacedJSONResourceAPISearchViewSet,
    basename="namespaced_indexable_search",
)

urlpatterns = router.urls
