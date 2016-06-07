##
## MAKEFILE VARIABLES
##

# Nodejs commands and flags
UGLIFY = node_modules/.bin/uglifyjs
UGLIFYFLAGS =
LESS = node_modules/.bin/lessc
LESSFLAGS = --compress
WATCHY = node_modules/.bin/watchy
WATCHYFLAGS = --wait 5 --no-init-spawn --silent

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
less_watch := \
	$(shell find less -name '*.less') \
	$(shell find $(bootstrap_path) -name '*.less')

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
assets: $(js_bundle) $(css_bundle)

.PHONY: watch
watch:
	$(WATCHY) $(WATCHYFLAGS) --watch js,less,vendor,Makefile -- make assets

$(js_bundle): $(js_sources)
	$(UGLIFY) $(UGLIFYFLAGS) $(js_sources) > $@

$(css_bundle): $(less_watch)
	$(LESS) $(LESSFLAGS) --include-path=$(bootstrap_path) $(less_source) > $@


##
## PYTHON/TEST RELATED
##
.PHONY: test
test:
	python manage.py test --verbosity 2

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
