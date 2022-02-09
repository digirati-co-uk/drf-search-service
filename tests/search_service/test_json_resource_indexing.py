import copy
import json
import pytest
import requests
from ..utils import is_responsive_404

app_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}
test_data_store = {}


def test_json_resource_create(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "A Test Resource",
        "data": {"key_1": "Value 1", "key_2": "Value 2"},
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json, 
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("label") == post_json.get("label")
    assert response_json.get("data") == post_json.get("data")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    test_data_store["json_resource_id"] = response_json.get("id")


def test_json_resource_get(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 200
    resource_id = test_data_store.get('json_resource_id')
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}/{resource_id}",
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("id") == resource_id


def test_json_resource_indexables_creation(http_service):
    """ """
    test_endpoint = "indexables"
    status = 200
    resource_id = test_data_store.get('json_resource_id')
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 3
    for indexable in response_json.get("results"):
        assert indexable.get("resource_id") == resource_id


def test_json_resource_simple_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "fulltext": "resource"
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) > 0


def test_json_resource_simple_query_no_match(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "fulltext": "digirati"
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_json_resource_simple_query_rank(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "fulltext": "resource"
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert int(response_json["results"][0].get("rank", 0)) > 0  # There is a non-zero rank


def test_json_resource_simple_query_snippet(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "fulltext": "resource"
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert "<b>Resource</b>" in response_json["results"][0].get("snippet", None)


def test_json_resource_facet_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {"facets": [{
        "type": "descriptive",
        "subtype": "key_1",
        "value": "Value 1"
    }]}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 1


def test_json_another_resource_create(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "Another item",
        "data": {"key_1": "Value 1", "key_3": "Value 3"},
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    assert response.status_code == status


def test_json_resource_another_facet_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {"facets": [{
        "type": "descriptive",
        "subtype": "key_1",
        "value": "Value 1"
    }]}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 2


def test_json_resource_facet_query_wrong_key(http_service):
    """
    Looking for a value, but it's stored in a different key
    """
    test_endpoint = "json_search"
    status = 200
    post_json = {"facets": [{
        "type": "descriptive",
        "subtype": "key_3",
        "value": "Value 1"
    }]}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_json_resource_simple_query_data_key(http_service):
    test_endpoint = "json_search"
    post_json = {
        "fulltext": "Value 3"
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert len(response_json.get("results")) == 1
    assert "<b>Value</b>" in response_json["results"][0].get("snippet", None)


def test_json_resource_simple_query_data_key_broader(http_service):
    test_endpoint = "json_search"
    post_json = {
        "fulltext": "Value"
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert len(response_json.get("results")) == 4
    assert "<b>Value</b>" in response_json["results"][0].get("snippet", None)


def test_json_resource_resource_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {  # Partial match on label, should match against "Another"
        "resource_filters": [{"value": "other", "field": "label", "operator": "icontains",
                              "resource_class": "jsonresource"}],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 1


def test_json_resource_resource_query_no_match(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "resource_filters": [{"value": "something", "field": "label", "operator": "icontains",
                              "resource_class": "jsonresource"}],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_json_resource_resource_query_no_resourceclass(http_service):
    """
    THis will 500 as there is no `foo` model defined in the application
    """
    test_endpoint = "json_search"
    status = 500
    post_json = {
        "resource_filters": [{"value": "other", "field": "label", "operator": "icontains",
                              "resource_class": "foo"}],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers
    )
    assert response.status_code == status
