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

deps:
	pip install -U pip-tools
	pip-compile --no-annotate --no-header --upgrade requirements/main.in >/dev/null
	pip-compile --no-annotate --no-header --upgrade requirements/prod.in >/dev/null

clean:
	docker ps -q -f status=exited | xargs docker rm
	docker images -q -f dangling=true | xargs docker rmi
	find inloop tests -name "*.pyc" -delete
	find inloop tests -name "__pycache__" -delete

purge: clean
	rm -rf .state
	-docker rmi $(IMAGE)

.PHONY: default coveragetest lint install-deps deps clean purge
