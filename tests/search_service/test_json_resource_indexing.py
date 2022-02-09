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

