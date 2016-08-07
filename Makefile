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
	vendor/bootstrap/js/alert.js \
	vendor/bootstrap/js/collapse.js \
	vendor/bootstrap/js/tab.js \
	vendor/prism/prism.js \
	vendor/prism/components/prism-java.js \
	vendor/jquery-timeago/jquery.timeago.js \
	vendor/jquery-refresh/jquery.refresh.js \
	vendor/anchorjs/anchor.js \
	js/inloop.js

# Target file for the CSS bundle
css_bundle := inloop/core/static/css/inloop.min.css

# Source file for the CSS bundle
bootstrap_path := vendor/bootstrap/less
less_source := less/inloop.less


# default target as a hint for the user
.PHONY: all
all:
	@echo Nothing to do -- please specify a target.


deps:
	pip-compile --no-annotate --no-header --upgrade requirements/main.in > /dev/null
	pip-compile --no-annotate --no-header --upgrade requirements/prod.in > /dev/null


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
## DOCKER HELPERS
##
.PHONY: docker-clean
docker-clean:
	-docker rm $(shell docker ps -q -f status=exited) >/dev/null 2>&1
	-docker rmi $(shell docker images -q -f dangling=true) >/dev/null 2>&1
