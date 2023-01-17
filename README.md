# drf-search-service

## API Structure

[/api](http://localhost:8000/api/)

## Local Development

An example Django project that includes the `search_service` is provided for development and testing. 

The docker-compose file(s) requires an .env file configured with the necessary variables, e.g.:

```.env
# General
MIGRATE=True
LOAD=False
DJANGO_DEBUG=True
WAITRESS=False
DJANGO_SUPERUSER_USERNAME=manifesto_admin
DJANGO_SUPERUSER_PASSWORD=manifesto_password
DJANGO_SUPERUSER_EMAIL=finlay.mccourt@digirati.com
INIT_SUPERUSER=False
# PostgreSQL
# ------------------------------------------------------------------------------
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres 
POSTGRES_PASSWORD=postgres_password
DATABASE_URL=postgres://postgres:postgres_password@postgres:5432/postgres

# Docker compose specific
DOCKER_COMPOSE_WEB_PORT=8000
```

To run just the app locally with docker-compose: 
```bash
docker-compose -f docker-compose.yml up
```

Dependencies for the example project are defined as part of the `dev` group in [pyproject.toml](pyproject.toml), to update the project requirements ([example_project/requirements.txt](example_project/requirements.txt)) after adding dependencies: 
```bash 
poetry export -f requirements.txt --output example_project/requirements.txt --without-hashes --with dev
``` 

## Running tests

The [tests](tests) directory contains tests which use `pytest-docker` to spin up the example project and perform integration tests with the `search_service` REST api's.

Dependencies required to run the tests are defined as part of the `test` group in [pyproject.toml](pyproject.toml), and need to be installed locally in order to run tests: 
```bash 
poetry install --only test
```

To update the pytest_requirements.txt: 
```bash 
poetry export -f requirements.txt --output tests/pytest_requirements.txt --only test
```
To run all the tests: 
```bash
cd ./tests/
poetry run pytest
```
To run an individual test file: 
```bash
cd ./tests/
poetry run pytest ./exemplar/test_resource_crud_api.py
```

nginx: 
Configured in /conf/nginx.conf
proxies `/` through to django app, and serves the `/app_static` and `/app_media` directories at `/static/` and `/media/`.

## Adding dependencies 

Poetry is used to manage dependencies and create the `requirements.txt` file used in the docker image to install python dependencies. To add a dependency through Poetry run (e.g.): 
```bash
poetry add djangorestframework
```
To add a git repository as a dependency, targeting a specific branch: 
```bash
poetry add git+https://github.com/digirati-co-uk/drf-search-service#develop
```
and then to create the `requirements.txt` file run: 
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes 
```
n.b. the `---without-hashes` option is only required when working with python libraries being installed from github. 


