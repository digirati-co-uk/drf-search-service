from rest_framework import routers

from .views import (
    ExemplarResourceViewSet,
)

app_name = "exemplar"
router = routers.DefaultRouter(trailing_slash=False)
router.register(
    "exemplar_resource", ExemplarResourceViewSet, basename="exemplar_resource"
)

urlpatterns = router.urls
