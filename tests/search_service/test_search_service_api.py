import copy
import json
import pytest
import requests
from ..utils import is_responsive_404


app_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}


@pytest.fixture(scope="session")
def http_service(docker_ip, docker_services):
    """
    Ensure that Django service is up and responsive.
    """

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("test_container", 8000)
    url = "http://{}:{}".format(docker_ip, port)
    url404 = f"{url}/missing"
    docker_services.wait_until_responsive(
        timeout=300.0, pause=0.1, check=lambda: is_responsive_404(url404)
    )
    return url


def test_indexables_list(http_service):
    """ """
    test_endpoint = "indexables"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    resp_data = response.json()
    assert response.status_code == status


def test_model_list(http_service):
    """ """
    test_endpoint = "model"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    resp_data = response.json()
    assert response.status_code == status


def test_iiif_list(http_service):
    """ """
    test_endpoint = "iiif"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    resp_data = response.json()
    assert response.status_code == status


def test_contexts_list(http_service):
    """ """
    test_endpoint = "contexts"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    resp_data = response.json()
    assert response.status_code == status


def test_iiif_instance(http_service, floco_manifest):
    """
    Create a single iiif item that can be used for various tests.

    :return: requests response
    """
    test_endpoint = "iiif"
    id = "d8a35385-d097-4306-89c0-1a15aa74e6da"
    image_service = floco_manifest["sequences"][0]["canvases"][0]["images"][0][
        "resource"
    ]["service"]["@id"]
    post_json = {
        "contexts": [  # List of contexts with their id and type
            {"id": "urn:florentinecodex:site:1", "type": "Site"},
            {"id": "FLorentine Codex", "type": "Collection"},
        ],
        "resource": floco_manifest,  # this is the JSON for the IIIF resource
        "id": f"urn:florentinecodex:manifest:{id}",  # Madoc ID for the subject/object
        "thumbnail": f"{image_service}/full/400,/0/default.jpg",  # Thumbnail URL
        "cascade": False,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    j = result.json()
    assert result.status_code == 201
    assert j.get("madoc_id") == f"urn:florentinecodex:manifest:{id}"
    assert (
        j.get("madoc_thumbnail")
        == "https://media.getty.edu/iiif/image/124afceb-1051-404a-91fb-df289963b74c/full/400,/0/default.jpg"
    )
    assert j.get("first_canvas_id") is not None
    assert j.get("first_canvas_json") is not None
