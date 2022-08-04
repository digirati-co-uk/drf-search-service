import json
import os
import pytest
import requests
import pathlib
import glob


from .utils import is_responsive_404


@pytest.fixture
def tests_dir():
    return pathlib.Path(__file__).resolve().parent


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return pathlib.Path(__file__).resolve().parent / "docker-compose.test.yml"


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


@pytest.fixture
def floco_manifest(tests_dir):
    return json.load((tests_dir / "fixtures/iiif/vol3.json").open(encoding="utf-8"))


@pytest.fixture
def lagq(tests_dir):
    return json.load((tests_dir / "fixtures/text/lagq.json").open(encoding="utf-8"))


@pytest.fixture
def na_en_ad(tests_dir):
    return json.load((tests_dir / "fixtures/text/na_en_ad.json").open(encoding="utf-8"))


@pytest.fixture
def na_ad(tests_dir):
    return json.load((tests_dir / "fixtures/text/na_ad.json").open(encoding="utf-8"))


@pytest.fixture
def tags(tests_dir):
    return json.load(
        (tests_dir / "fixtures/tags/tags_truncated.json").open(encoding="utf-8")
    )
