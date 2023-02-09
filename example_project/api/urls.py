from django.urls import path, include
from rest_framework import routers

from search_service.urls.api import (
    sandboxed_router,
)


class ExampleProjectAPIRootView(routers.APIRootView):
    """
    REST APIs for the Example Project API app.
    """

    pass


class ExampleProjectAPIRouter(routers.DefaultRouter):
    APIRootView = ExampleProjectAPIRootView

    def get_api_root_view(self, api_urls=None):
        return self.APIRootView.as_view(
            api_root_dict={
                "search_service": "search_service:api-root",
                # "sandboxed_search_service": "search_service:api-root",
            }
        )


router = ExampleProjectAPIRouter()

app_name = "api"

include_urls = [
    path("search_service/", include("search_service.urls.api")),
    path("search_service/sandboxed/", include(sandboxed_router.urls)),
]
urlpatterns = router.urls + include_urls
