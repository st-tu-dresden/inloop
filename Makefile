IMAGE   := inloop-integration-test
SOURCES := inloop tests

ifndef TRAVIS
override TESTOPTS += --exclude-tag=slow
endif

# The default TMPDIR on macOS, /var/folders/..., cannot
# be exported from macOS to Docker, but /tmp can.
ifeq ($(shell uname -s),Darwin)
override TESTENV += TMPDIR=/tmp
endif

init:
	poetry install
	docker build -t $(IMAGE) tests/testrunner

run:
	poetry run honcho -f Procfile.dev start

loaddb:
	poetry run ./manage.py migrate
	poetry run ./manage.py loaddata about_pages staff_group
	poetry run ./manage.py loaddata demo_accounts development_site

test:
	poetry run ./manage.py test $(TESTOPTS)

coverage:
	poetry run coverage run ./manage.py test $(TESTOPTS)
	poetry run coverage report

lint:
	poetry run $(SHELL) -c 'isort --check-only --recursive $(SOURCES) && flake8 $(SOURCES)'

.PHONY: init loaddb test coverage lint
