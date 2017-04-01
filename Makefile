IMAGE := inloop-integration-test
SUITE := tests

PYTHON := python3.5
PYTAG  := $(shell echo $(PYTHON) | sed 's/thon//;s/\.//')
VENV   := $(PWD)/.venvs/$(PYTAG)

default:
	@echo "Please specify a Makefile target."
	@exit 1

coveragetest: .state/docker
	coverage run manage.py test --failfast $(SUITE)

lint:
	isort --quiet --check-only
	flake8

install-deps:
	pip install -r requirements/main.txt
	pip install -r requirements/test.txt
	pip install -r requirements/lint.txt
	npm install --production

install-tools:
	pip install -r requirements/dev.txt

.state/docker: tests/functional/testrunner/Dockerfile
	docker build -t $(IMAGE) tests/functional/testrunner
	mkdir -p .state
	touch .state/docker

virtualenv:
	rm -rf $(VENV)
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -U pip setuptools

initdb:
	mkdir -p .state
	python manage.py migrate
	python manage.py createsuperuser --username admin --email admin@localhost

devenv: virtualenv
	-cp -i .env_develop .env
	PATH=$(VENV)/bin:$(PATH) make install-deps install-tools initdb
	@echo
	@echo "virtualenv created -- now run 'source $(VENV)/bin/activate'."
	@echo

deps:
	pip-compile --no-annotate --no-header --upgrade requirements/main.in >/dev/null
	pip-compile --no-annotate --no-header --upgrade requirements/prod.in >/dev/null

clean:
	docker ps -q -f status=exited | xargs docker rm
	docker images -q -f dangling=true | xargs docker rmi
	find inloop tests -name "*.pyc" -delete
	find inloop tests -name "__pycache__" -delete

purge: clean
	rm -rf .state .venvs .env node_modules
	-docker rmi $(IMAGE)

.PHONY: default coveragetest lint install-deps install-tools virtualenv initdb devenv deps clean purge
