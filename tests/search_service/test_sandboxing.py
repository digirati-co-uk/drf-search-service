import pytest
import requests
import collections

api_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}
test_data_store = collections.defaultdict(list)


def test_sandboxed_json_resource_create(http_service):
    """ """
    contexts = ["urn:test:value:1"]
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "A Test Resource",
        "data": {"key_1": "Value 1", "key_2": "Value 2"},
        "contexts": contexts,
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
    assert response_json.get("contexts") == contexts
    test_data_store["json_resource_id"] = response_json.get("id")


def test_context_created(http_service):
    """ """
    contexts = ["urn:test:value:1"]
    test_endpoint = "context"
    status = 200
    for ns_urn in contexts:
        response = requests.get(
            f"{http_service}/{api_endpoint}/{test_endpoint}/{ns_urn}",
            headers=test_headers,
        )
        response_json = response.json()
        assert response.status_code == status
        assert response_json.get("urn") == ns_urn


def test_sandboxed_json_resource_indexables_creation(http_service):
    contexts = ["urn:test:value:1"]
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
        assert indexable.get("contexts") == contexts

    """ """


@pytest.mark.parametrize(
    "context,label",
    [
        ("urn:test:value:3", "Test Resource 1"),
        ("urn:test:value:3", "Test Resource 2"),
        ("urn:test:value:3", "Test Resource 3"),
        ("urn:test:value:4", "Test Resource 1"),
        ("urn:test:value:4", "Test Resource 2"),
        ("urn:test:value:5", "Test Resource 1"),
    ],
)
def test_sandboxed_json_resource_context_header_create(
    http_service, context, label
):
    test_endpoint = "sandboxed/json_resource"
    sandboxed_headers = {"x-context": context, **test_headers}
    status = 201
    post_json = {
        "label": label,
        "data": {"key_1": "Value 1", "key_2": "Value 2"},
    }
    response = requests.post(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=sandboxed_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("label") == post_json.get("label")
    assert response_json.get("data") == post_json.get("data")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    assert response_json.get("contexts") == [context]
    test_data_store[context].append(response_json.get("id"))


def test_sandboxed_json_resource_list_auth_fail(http_service):
    test_endpoint = "sandboxed/json_resource"
    status = 403
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("detail") == "x-context header not present on request."


@pytest.mark.parametrize(
    "context",
    [
        ("urn:test:value:3"),
        ("urn:test:value:4"),
        ("urn:test:value:5"),
    ],
)
def test_sandboxed_json_resource_context_header_list(http_service, context):
    test_endpoint = "sandboxed/json_resource"
    sandboxed_headers = {"x-context": context, **test_headers}
    status = 200
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/",
        headers=sandboxed_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == len(test_data_store.get(context))
    for r in response_json.get("results"):
        assert r.get("id") in test_data_store.get(context)


@pytest.mark.parametrize(
    "context",
    [
        ("urn:test:value:3"),
        ("urn:test:value:4"),
        ("urn:test:value:5"),
    ],
)
def test_sandboxed_json_resource_context_header_detail(http_service, context):
    resource_id = test_data_store[context][0]
    test_endpoint = "sandboxed/json_resource"
    sandboxed_headers = {"x-context": context, **test_headers}
    status = 200
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/{resource_id}/",
        headers=sandboxed_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("id") == resource_id


@pytest.mark.parametrize(
    "access_context,target_context",
    [
        ("urn:test:value:3", "urn:test:value:4"),
        ("urn:test:value:4", "urn:test:value:5"),
        ("urn:test:value:5", "urn:test:value:3"),
    ],
)
def test_sandboxed_json_resource_context_header_detail_wrong_context(
    http_service, access_context, target_context
):
    resource_id = test_data_store[target_context][0]
    test_endpoint = "sandboxed/json_resource"
    sandboxed_headers = {"x-context": access_context, **test_headers}
    status = 404
    response = requests.get(
        f"{http_service}/{api_endpoint}/{test_endpoint}/{resource_id}/",
        headers=sandboxed_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("detail") == "Not found."

@pytest.mark.parametrize(
    "access_context,target_context",
    [
        ("urn:test:value:3", "urn:test:value:4"),
        ("urn:test:value:4", "urn:test:value:5"),
        ("urn:test:value:5", "urn:test:value:3"),
    ],
)
def test_sandboxed_json_resource_context_header_delete_wrong_context(
    http_service, access_context, target_context
):
    resource_id = test_data_store[target_context][0]
    test_endpoint = "sandboxed/json_resource"
    sandboxed_headers = {"x-context": access_context, **test_headers}
    status = 404
    response = requests.delete(
        f"{http_service}/{api_endpoint}/{test_endpoint}/{resource_id}/",
        headers=sandboxed_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("detail") == "Not found."


def test_sandboxed_json_resource_cleanup(http_service):
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
