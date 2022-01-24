from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.schemas import get_schema_view
from rest_framework import routers

from .views import (
        api_root, 
        IndexablesList, 
        IndexablesDetail, 
        ModelList, 
        ModelDetail, 
        IIIFSearch, 
        Autocomplete, 
        Facets, 
        IIIFList, 
        IIIFDetail, 
        ContextList, 
        ContextDetail,
        )

app_name = "search_service"
router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", api_root),
    path("indexables", IndexablesList.as_view(), name="indexables_list"),
    path("indexables/<int:pk>", IndexablesDetail.as_view(), name="indexables_detail"),
    path("model", ModelList.as_view(), name="model_list"),
    path("model/<int:pk>", ModelDetail.as_view(), name="model_detail"),
    path("search", IIIFSearch.as_view({"get": "list", "post": "list"}), name="search"),
    path("autocomplete", Autocomplete.as_view({"get": "list", "post": "list"}), name="autocomplete"),
    path("facets", Facets.as_view({"get": "list", "post": "list"}), name="facets"),
    path("iiif", IIIFList.as_view(), name="iiifresource_list"),
    path("iiif/<str:pk>", IIIFDetail.as_view(), name="iiifresource_detail"),
    path("contexts", ContextList.as_view(), name="context_list"),
    path("contexts/<slug:slug>", ContextDetail.as_view(), name="context_detail"),
    path("openapi", get_schema_view(title="IIIF Search", description="IIIF Search API", version="0.0.1"), name="openapi_schema")
]

urlpatterns = format_suffix_patterns(urlpatterns)
urlpatterns += [path("api-auth/", include("rest_framework.urls"))]
