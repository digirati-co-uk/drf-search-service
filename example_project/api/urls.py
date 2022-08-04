from django.urls import path, include
from rest_framework import routers

from search_service.urls.api import (
    namespaced_router,
)

app_name = "api"
router = routers.DefaultRouter(trailing_slash=False)
include_urls = [
    path("search_service/", include("search_service.urls.api")),
    path("search_service/namespaced/", include(namespaced_router.urls)),
]
urlpatterns = router.urls + include_urls
