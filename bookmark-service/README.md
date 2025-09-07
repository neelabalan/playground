# Bookmark Service

> For reference

## Setup

### To install poetry

`curl -sSL https://install.python-poetry.org | python3 -`


### Contributing

Run `poetry install` to install the env.

Run `poetry run pre-commit install` to initialize the git hooks.

Run `poetry run pre-commit run --all-files` if there are file that were committed before adding the git hooks.

## Start the service

`docker-compose build`

`docker-compose run bookmark`

### Run tests

`docker-compose run tests`

