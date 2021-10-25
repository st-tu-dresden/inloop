help: 	## Show this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "%-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: 	## Initialize the virtualenv and install packages.
	poetry install

loaddb: ## Create SQLite database from schema and load fixtures.
	poetry run ./manage.py migrate
	poetry run ./manage.py loaddata about_pages staff_group
	poetry run ./manage.py loaddata demo_accounts development_site

run:	## Run the development webserver and the task queue.
	@poetry run honcho -f Procfile.dev start || true

test:	## Run the backend tests via nox.
	nox -r --session tests

lint:	## Run the Python linters via nox.
	nox -r --session lint

.PHONY: help init loaddb test lint
