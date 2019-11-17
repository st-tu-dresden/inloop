#!/usr/bin/env bash

function fail {
    printf "%s\n" "$1" >&2
    exit 1
}

if [[ ${HTMLVALIDATOR_ENABLED} = 1 ]]; then
    if [[ -z ${HTMLVALIDATOR_VNU_CLASSPATH} ]]; then
        fail "The vnu validator is enabled, but no classpath was given."
    fi

    if [[ -z ${HTMLVALIDATOR_VNU_PORT} ]]; then
        fail "The vnu validator is enabled, but no port was given."
    fi

    java -cp ${HTMLVALIDATOR_VNU_CLASSPATH} nu.validator.servlet.Main ${HTMLVALIDATOR_VNU_PORT}

    exit $?
else
    echo "The vnu validator can be enabled by setting the corresponding env variable."
    # Sleep forever to prevent other workers from exiting
    while true; do sleep 86400; done
fi
