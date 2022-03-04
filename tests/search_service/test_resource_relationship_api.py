import requests

app_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}
test_data_store = {}


def test_resource_relationship_list_empty(http_service):
    test_endpoint = "resource_relationship"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert response_json.get("results") == []


def test_resource_relationship_create_resources_for_resource_relationship(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "Parent",
        "data": {},
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("label") == post_json.get("label")
    assert response_json.get("data") == post_json.get("data")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    test_data_store["parent_id"] = response_json.get("id")

    post_json = {
        "label": "Child",
        "data": {},
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("label") == post_json.get("label")
    assert response_json.get("data") == post_json.get("data")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    test_data_store["child_id"] = response_json.get("id")

def test_resource_relationship_create_resource_relationship(http_service):
    """ """
    test_endpoint = "resource_relationship"
    status = 201
    post_json = {
        "source_id": test_data_store.get("child_id"),
        "source_content_type": 7,
        "target_id": test_data_store.get("child_id"),
        "target_content_type": 7,
        "type": "partOf",
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("type") == post_json.get("type")
    assert response_json.get("source_id") == post_json.get("source_id")
    assert response_json.get("target_id") == post_json.get("target_id")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    test_data_store["relationship_id"] = response_json.get("id")

def test_resource_relationship_list(http_service):
    test_endpoint = "resource_relationship"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 1
    relationship = response_json["results"][0]
    assert relationship.get("id") == test_data_store.get("relationship_id")

def test_resource_relationship_get(http_service):
    test_endpoint = f"resource_relationship/{test_data_store.get('relationship_id')}"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("id") == test_data_store.get("relationship_id")
    assert response_json.get("source_id") == test_data_store.get("child_id")
    assert response_json.get("target_id") == test_data_store.get("parent_id")
    assert response_json.get("type") == "partOf"


def test_resource_relationship_delete_resources_for_relationship(http_service):
    test_endpoint = f"json_resource/{test_data_store.get('parent_id')}"
    status = 204
    response = requests.delete(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status

    test_endpoint = f"json_resource/{test_data_store.get('child_id')}"
    status = 204
    response = requests.delete(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status

def test_resource_relationship_deleted(http_service):
    test_endpoint = f"resource_relationship/{test_data_store.get('relationship_id')}"
    status = 404
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
