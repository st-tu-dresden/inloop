#!/usr/bin/env bash

CSS_FILES=$(find ./assets -type f -name "*.css" -not -name "*.min.css" -not -path "*/vendor/*")
for f in ${CSS_FILES}; do
    echo "Checking ${f}"
    csslint --format=compact ${f}
done
