import requests
import pytest

app_endpoint = "api/search_service"
public_endpoint = "search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}
test_data_store = {"json_resource": []}


def get_content_type(http_service, app_label, model):
    response = requests.get(
        f"{http_service}/api/search_service/content_type/",
        headers=test_headers,
    )
    response_json = response.json()
    for c_type in response_json.get("results"):
        if c_type.get("app_label") == app_label and c_type.get("model") == model:
            return c_type.get("id")
    return None


@pytest.mark.parametrize(
    "parent_resource, child_resources",
    [
        (
            {
                "label": "Parent resource vowels",
                "type": "parent",
                "contexts": ["urn:madoc:parent:1"],
                "data": {
                    "indexables": [
                        {
                            "type": "metadata",
                            "subtype": "language",
                            "original_content": "Greek",
                            "indexable_text": "Greek",
                        }
                    ],
                },
            },
            [
                {
                    "label": "Child resource alpha",
                    "contexts": ["urn:madoc:parent:1", "urn:madoc:child:1"],
                    "type": "child",
                    "data": {},
                },
                {
                    "label": "Child resource omicron",
                    "contexts": ["urn:madoc:parent:1", "urn:madoc:child:2"],
                    "type": "child",
                    "data": {},
                },
            ],
        ),
        (
            {
                "label": "Parent resource consonants",
                "type": "parent",
                "contexts": ["urn:madoc:parent:2"],
                "data": {
                    "indexables": [
                        {
                            "type": "metadata",
                            "subtype": "language",
                            "original_content": "Greek",
                            "indexable_text": "Greek",
                        }
                    ],
                },
            },
            [
                {
                    "label": "Child resource beta",
                    "contexts": ["urn:madoc:parent:2", "urn:madoc:child:3"],
                    "type": "child",
                    "data": {},
                },
                {
                    "label": "Child resource gamma",
                    "contexts": ["urn:madoc:parent:2", "urn:madoc:child:4"],
                    "type": "child",
                    "data": {},
                },
            ],
        ),
        (
            {
                "label": "Parent resource numbers",
                "type": "parent",
                "contexts": ["urn:madoc:parent:3"],
                "data": {
                    "indexables": [
                        {
                            "type": "metadata",
                            "subtype": "language",
                            "original_content": "English",
                            "indexable_text": "English",
                        }
                    ],
                },
            },
            [
                {
                    "label": "Child resource one",
                    "contexts": ["urn:madoc:parent:3", "urn:madoc:child:5"],
                    "type": "child",
                    "data": {},
                },
                {
                    "label": "Child resource two",
                    "contexts": ["urn:madoc:parent:3", "urn:madoc:child:6"],
                    "type": "child",
                    "data": {},
                },
            ],
        ),
    ],
)
def test_create_related_resources(http_service, parent_resource, child_resources):
    """ """
    resource_endpoint = "json_resource"
    relationship_endpoint = "resource_relationship"
    rel_content_type = get_content_type(http_service, "search_service", "jsonresource")
    status = 201
    response = requests.post(
        f"{http_service}/{app_endpoint}/{resource_endpoint}/",
        json=parent_resource,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("label") == parent_resource.get("label")
    assert response_json.get("data") == parent_resource.get("data")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    parent_id = response_json.get("id")
    test_data_store["json_resource"].append(parent_id)
    for child in child_resources:
        response = requests.post(
            f"{http_service}/{app_endpoint}/{resource_endpoint}/",
            json=child,
            headers=test_headers,
        )
        response_json = response.json()
        assert response.status_code == status
        assert response_json.get("label") == child.get("label")
        assert response_json.get("data") == child.get("data")
        assert response_json.get("created") is not None
        assert response_json.get("modified") is not None
        assert response_json.get("id") is not None
        child_id = response_json.get("id")
        test_data_store["json_resource"].append(child_id)
        relationship_post = {
            "source_id": parent_id,
            "source_content_type": rel_content_type,
            "target_id": child_id,
            "target_content_type": rel_content_type,
            "type": "hasChild",
        }
        rel_response = requests.post(
            f"{http_service}/{app_endpoint}/{relationship_endpoint}/",
            json=relationship_post,
            headers=test_headers,
        )
        rel_response_json = rel_response.json()
        assert rel_response.status_code == status
        assert rel_response_json.get("type") == relationship_post.get("type")
        assert rel_response_json.get("source_id") == relationship_post.get("source_id")
        assert rel_response_json.get("target_id") == relationship_post.get("target_id")
        assert rel_response_json.get("created") is not None
        assert rel_response_json.get("modified") is not None
        assert rel_response_json.get("id") is not None


@pytest.mark.parametrize("resource_type, count", [("parent", 3), ("child", 6)])
def test_json_resource_search_by_type(http_service, resource_type, count):
    """ """
    test_endpoint = "json_resource_search"
    post_json = {
        "fulltext": "resource",
        "raw": {"type__iexact": resource_type},
    }
    response = requests.post(
        f"{http_service}/{public_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == count


@pytest.mark.parametrize("resource_type, count", [("parent", 3), ("child", 6)])
def test_json_resource_search_by_raw_type(http_service, resource_type, count):
    """ """
    test_endpoint = "json_resource_search"
    post_json = {
        "fulltext": "resource",
        "raw": {"type__iexact": resource_type},
    }
    response = requests.post(
        f"{http_service}/{public_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == count


@pytest.mark.parametrize("resource_type, count", [("parent", 3), ("child", 6)])
def test_json_resource_search_by_resource_type(http_service, resource_type, count):
    """ """
    test_endpoint = "json_resource_search"
    post_json = {
        "fulltext": "resource",
        "resource_filters": [
            {
                "resource_class": "jsonresource",
                "field": "type",
                "operator": "iexact",
                "value": resource_type,
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{public_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == count


@pytest.mark.parametrize(
    "context_urn, count", [("urn:madoc:parent:1", 3), ("urn:madoc:child:1", 1)]
)
def test_json_resource_search_by_context_urn(http_service, context_urn, count):
    """ """
    test_endpoint = "json_resource_search"
    post_json = {
        "fulltext": "resource",
        "contexts": [context_urn],
    }
    response = requests.post(
        f"{http_service}/{public_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == count


def test_cleanup_resource(http_service):
    status = 204
    for resource_id in test_data_store.get("json_resource"):
        response = requests.delete(
            f"{http_service}/{app_endpoint}/json_resource/{resource_id}",
            headers=test_headers,
        )
        assert response.status_code == status
