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
	pipenv sync --dev
	docker build -t $(IMAGE) tests/testrunner
	ln -snf .env.develop .env

run:
	pipenv run honcho start

loaddb:
	pipenv run ./manage.py migrate
	pipenv run ./manage.py loaddata about_pages staff_group
	pipenv run ./manage.py loaddata demo_accounts development_site

test:
	pipenv run ./manage.py test $(TESTOPTS)

coverage:
	pipenv run coverage run ./manage.py test $(TESTOPTS)
	pipenv run coverage report

lint:
	pipenv run $(SHELL) -c 'isort --check-only --recursive $(SOURCES) && flake8 $(SOURCES)'

.PHONY: init loaddb test coverage lint
