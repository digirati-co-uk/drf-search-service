import pytest
import requests
import collections

api_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}
test_data_store = collections.defaultdict(list)


def test_namespaced_json_resource_create(http_service):
    """ """
    namespaces = ["urn:test:value:1"]
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "A Test Resource",
        "data": {"key_1": "Value 1", "key_2": "Value 2"},
        "namespaces": namespaces,
    }
    response = requests.post(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
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
    assert response_json.get("namespaces") == namespaces
    test_data_store["json_resource_id"] = response_json.get("id")


def test_namespace_created(http_service):
    """ """
    namespaces = ["urn:test:value:1"]
    test_endpoint = "namespace"
    status = 200
    for ns_urn in namespaces:
        response = requests.get(
            f"{http_service}/{api_endpoint}/{test_endpoint}/{ns_urn}",
            headers=test_headers,
        )
        response_json = response.json()
        assert response.status_code == status
        assert response_json.get("urn") == ns_urn


def test_namespaced_json_resource_indexables_creation(http_service):
    namespaces = ["urn:test:value:1"]
    test_endpoint = "indexable"
    status = 200
    resource_id = test_data_store.get("json_resource_id")
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/", headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 3
    for indexable in response_json.get("results"):
        assert indexable.get("resource_id") == resource_id
        assert indexable.get("namespaces") == namespaces

    """ """


@pytest.mark.parametrize(
    "namespace,label",
    [
        ("urn:test:value:3", "Test Resource 1"),
        ("urn:test:value:3", "Test Resource 2"),
        ("urn:test:value:3", "Test Resource 3"),
        ("urn:test:value:4", "Test Resource 1"),
        ("urn:test:value:4", "Test Resource 2"),
        ("urn:test:value:5", "Test Resource 1"),
    ],
)
def test_namespaced_json_resource_namespace_header_create(
    http_service, namespace, label
):
    test_endpoint = "namespaced/json_resource"
    namespaced_headers = {"x-namespace": namespace, **test_headers}
    status = 201
    post_json = {
        "label": label,
        "data": {"key_1": "Value 1", "key_2": "Value 2"},
    }
    response = requests.post(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=namespaced_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("label") == post_json.get("label")
    assert response_json.get("data") == post_json.get("data")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    assert response_json.get("namespaces") == [namespace]
    test_data_store[namespace].append(response_json.get("id"))


def test_namespaced_json_resource_list_auth_fail(http_service):
    test_endpoint = "namespaced/json_resource"
    status = 403
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("detail") == "x-namespace header not present on request."


@pytest.mark.parametrize(
    "namespace",
    [
        ("urn:test:value:3"),
        ("urn:test:value:4"),
        ("urn:test:value:5"),
    ],
)
def test_namespaced_json_resource_namespace_header_list(http_service, namespace):
    test_endpoint = "namespaced/json_resource"
    namespaced_headers = {"x-namespace": namespace, **test_headers}
    status = 200
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
        headers=namespaced_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == len(test_data_store.get(namespace))
    for r in response_json.get("results"):
        assert r.get("id") in test_data_store.get(namespace)


@pytest.mark.parametrize(
    "namespace",
    [
        ("urn:test:value:3"),
        ("urn:test:value:4"),
        ("urn:test:value:5"),
    ],
)
def test_namespaced_json_resource_namespace_header_detail(http_service, namespace):
    resource_id = test_data_store[namespace][0]
    test_endpoint = "namespaced/json_resource"
    namespaced_headers = {"x-namespace": namespace, **test_headers}
    status = 200
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/{resource_id}/",
        headers=namespaced_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("id") == resource_id


@pytest.mark.parametrize(
    "access_namespace,target_namespace",
    [
        ("urn:test:value:3", "urn:test:value:4"),
        ("urn:test:value:4", "urn:test:value:5"),
        ("urn:test:value:5", "urn:test:value:3"),
    ],
)
def test_namespaced_json_resource_namespace_header_detail_wrong_namespace(
    http_service, access_namespace, target_namespace
):
    resource_id = test_data_store[target_namespace][0]
    test_endpoint = "namespaced/json_resource"
    namespaced_headers = {"x-namespace": access_namespace, **test_headers}
    status = 404
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/{resource_id}/",
        headers=namespaced_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("detail") == "Not found."

@pytest.mark.parametrize(
    "access_namespace,target_namespace",
    [
        ("urn:test:value:3", "urn:test:value:4"),
        ("urn:test:value:4", "urn:test:value:5"),
        ("urn:test:value:5", "urn:test:value:3"),
    ],
)
def test_namespaced_json_resource_namespace_header_delete_wrong_namespace(
    http_service, access_namespace, target_namespace
):
    resource_id = test_data_store[target_namespace][0]
    test_endpoint = "namespaced/json_resource"
    namespaced_headers = {"x-namespace": access_namespace, **test_headers}
    status = 404
    response = requests.delete(
        f"{http_service}/{api_endpoint}/{test_endpoint}/{resource_id}/",
        headers=namespaced_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("detail") == "Not found."


def test_namespaced_json_resource_cleanup(http_service):
    # Get a list of all resources
    test_endpoint = "json_resource"
    status = 200
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    # Delete all resources
    for resource_id in [res.get("id") for res in response_json.get("results")]:
        test_endpoint = f"json_resource/{resource_id}"
        status = 204
        response = requests.delete(
            f"{http_service}/{api_endpoint}/{test_endpoint}/", headers=test_headers
        )
        assert response.status_code == status
    # Check indexables have also been deleted
    test_endpoint = "indexable"
    status = 200
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/", headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0
