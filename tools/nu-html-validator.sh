#!/bin/sh
#
# Runs the vnu html validator if activated, idles otherwise.
#

die() {
    echo "Error: $@" >&2
    exit 1
}

if [ "$VALIDATE_HTML" = "1" ]; then
    [ -z "$VNU_JAR" ]  && die "The vnu validator is enabled, but no .jar file was given."
    [ -z "$VNU_PORT" ] && die "The vnu validator is enabled, but no port was given."

    exec java -Dnu.validator.servlet.bind-address=127.0.0.1 \
        -cp "$VNU_JAR" nu.validator.servlet.Main "$VNU_PORT"
fi

echo "HTML validation not active, export VALIDATE_HTML=1 to enable it"
read _exit  # for honcho, waits infinitely for input
