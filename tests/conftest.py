import json
import os
import pytest
import requests
import pathlib


@pytest.fixture
def tests_dir():
    return pathlib.Path(__file__).resolve().parent


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return pathlib.Path(__file__).resolve().parent / "docker-compose.test.yml"

