import copy
import json
import pytest
import requests
from tests.utils import is_responsive_404


app_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}

pytest.skip("skipping because this won't work on generic search", allow_module_level=True)


def test_json_resource_list(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    resp_data = response.json()
    assert response.status_code == status


def test_indexables_list(http_service):
    """ """
    test_endpoint = "indexables"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    resp_data = response.json()
    assert response.status_code == status


def test_contexts_list(http_service):
    """ """
    test_endpoint = "context"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    resp_data = response.json()
    assert response.status_code == status
