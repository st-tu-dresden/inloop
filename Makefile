IMAGE := inloop-integration-test
SUITE := tests

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

.state/docker: tests/functional/testrunner/Dockerfile
	docker build -t $(IMAGE) tests/functional/testrunner
	mkdir -p .state
	touch .state/docker

.PHONY: default coveragetest lint install-deps
