#!/usr/bin/env bash

JS_FILES=$(find ./assets -type f -name "*.js" -not -name "*.min.js" -not -path "*/vendor/*")
for f in ${JS_FILES}; do
    echo "Checking ${f}"
    jshint ${f}
done
