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
