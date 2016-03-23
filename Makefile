##
## MAKEFILE VARIABLES
##

# Nodejs commands and flags
UGLIFY = node_modules/.bin/uglifyjs
UGLIFYFLAGS =
LESS = node_modules/.bin/lessc
LESSFLAGS= --compress --include-path=vendor/bootstrap/less
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
less_sources := less/inloop.less

##
## MAKEFILE TARGETS
##

$(js_bundle): $(js_sources)
	@$(UGLIFY) $(UGLIFYFLAGS) $(js_sources) > $@

$(css_bundle): $(less_sources)
	@$(LESS) $(LESSFLAGS) $(less_sources) > $@

npm:
	@npm install >/dev/null

assets: npm $(js_bundle) $(css_bundle)

watch:
	@$(WATCHY) $(WATCHYFLAGS) --watch js,less,vendor,Makefile -- make assets

test:
	@python manage.py test --verbosity 2 --failfast

coverage:
	@coverage run manage.py test
	@coverage html

.PHONY: npm assets watch test coverage
