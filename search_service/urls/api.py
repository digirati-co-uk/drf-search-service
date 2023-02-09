"""
search_service/urls/api.py - DefaultRouter registration of API Viewsets.  
"""

from rest_framework import routers

from ..views import (
    JSONResourceAPIViewSet,
    ContextAPIViewSet,
    IndexableAPIViewSet,
    ResourceRelationshipAPIViewSet,
    ContentTypeAPIViewSet,
    IndexableAPISearchViewSet,
    JSONResourceAPISearchViewSet,
    # Sandboxed viewsets
    SandboxedJSONResourceAPIViewSet,
    SandboxedIndexableAPIViewSet,
    SandboxedIndexableAPISearchViewSet,
    SandboxedJSONResourceAPISearchViewSet,
)

app_name = "search_service"


class SearchServiceAPIRootView(routers.APIRootView):
    """
    REST APIs for the Search Service API app.
    """

    pass


class SearchServiceAPIRouter(routers.DefaultRouter):
    APIRootView = SearchServiceAPIRootView


router = SearchServiceAPIRouter()
router.register("indexable", IndexableAPIViewSet)
router.register("context", ContextAPIViewSet)
router.register("resource_relationship", ResourceRelationshipAPIViewSet)
router.register("content_type", ContentTypeAPIViewSet)
router.register("json_resource", JSONResourceAPIViewSet)
router.register(
    "indexable_search", IndexableAPISearchViewSet, basename="indexable_search"
)
router.register(
    "json_resource_search",
    JSONResourceAPISearchViewSet,
    basename="jsonresource_search",
)

# Only included in the example_project for testing
# Authentication classes should be set globally,
# or directly on inheriting ViewSets (as below) if namespacing is required
sandboxed_router = routers.DefaultRouter()
sandboxed_router.register(
    "indexable", SandboxedIndexableAPIViewSet, basename="sandboxed_indexable"
)
sandboxed_router.register(
    "json_resource",
    SandboxedJSONResourceAPIViewSet,
    basename="sandboxed_jsonresource",
)
sandboxed_router.register(
    "indexable_search",
    SandboxedIndexableAPISearchViewSet,
    basename="sandboxed_indexable_search",
)
sandboxed_router.register(
    "json_resource_search",
    SandboxedJSONResourceAPISearchViewSet,
    basename="sandboxed_jsonresource_search",
)

urlpatterns = router.urls
