from django.urls import path, include
from rest_framework import routers

from search_service.urls.api import (
    sandboxed_router,
)

app_name = "api"
router = routers.DefaultRouter(trailing_slash=False)
include_urls = [
    path("search_service/", include("search_service.urls.api")),
    path("search_service/sandboxed/", include(sandboxed_router.urls)),
]
urlpatterns = router.urls + include_urls
