##
## MAKEFILE VARIABLES
##

# Nodejs commands
uglifyjs := node_modules/.bin/uglifyjs
lessc := node_modules/.bin/lessc

# Target file for the JS bundle
js_bundle := inloop/core/static/js/inloop.min.js

# Javascript source files to be combined
# (order is important: jQuery > other 3rd party JS > INLOOP JS)
js_sources := \
	vendor/jquery/dist/jquery.min.js \
	vendor/bootstrap/dist/js/bootstrap.min.js \
	vendor/ace/src/ace.js \
	vendor/ace/src/mode-java.js \
	vendor/prism/prism.js \
	vendor/prism/components/prism-java.js \
	vendor/anchorjs/anchor.js \
	$(shell find js -name '*.js')

# Target file for the CSS bundle
css_bundle := inloop/core/static/css/inloop.min.css

# Source file for the CSS bundle
bootstrap_path := vendor/bootstrap/less
less_source := less/inloop.less

# Source and target directories for git hook setup
hook_source := support/git-hooks
hook_target := .git/hooks


# default target as a hint for the user
.PHONY: all
all:
	@echo Nothing to do -- please specify a target.


##
## ASSET MANAGEMENT
##
.PHONY: assets
assets: bundlecss bundlejs

.PHONY: bundlecss
bundlecss:
	$(lessc) --autoprefix="last 4 versions" --clean-css \
		--include-path=$(bootstrap_path) $(less_source) $(css_bundle)

.PHONY: bundlejs
bundlejs:
	$(uglifyjs) $(js_sources) --comment --output $(js_bundle)

.PHONY: watch
watch:
	watchmedo shell-command --patterns="*.less;*.js" \
		--recursive --command "make assets" less js


##
## PYTHON/TEST RELATED
##
.PHONY: test
test:
	python manage.py test

.PHONY: coverage
coverage:
	coverage run manage.py test
	coverage html


##
## GIT HOOK INSTALLATION
##
.PHONY: hookup
hookup:
	install -b -m 755 $(hook_source)/commit-msg $(hook_target)
	install -b -m 755 $(hook_source)/pre-commit $(hook_target)

.PHONY: hookup-all
hookup-all: hookup
	install -b -m 755 $(hook_source)/post-checkout $(hook_target)

.PHONY: unhookup
unhookup:
	rm -f $(hook_target)/commit-msg
	rm -f $(hook_target)/pre-commit
	rm -f $(hook_target)/post-checkout


##
## DOCKER HELPERS
##
.PHONY: docker-image
docker-image:
	$(MAKE) -C inloop/tasks/tests/docker

.PHONY: docker-clean
docker-clean:
	-docker rm $(shell docker ps -q -f status=exited) >/dev/null 2>&1
	-docker rmi $(shell docker images -q -f dangling=true) >/dev/null 2>&1
