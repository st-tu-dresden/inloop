#!/usr/bin/env bash
INSTALL_CMD="${INSTALL_CMD:-sudo apt-get install}"
PKGS_BASE="build-essential git python3 python3-dev python3-venv redis-server"
PKGS_PROD="$PKGS_BASE libpq-dev daemontools"
PKGS_DEV="$PKGS_BASE nodejs nodejs-legacy npm"

case "$1" in
    --dev)
        CMD="$INSTALL_CMD $PKGS_DEV"
        ;;
    --prod)
        CMD="$INSTALL_CMD $PKGS_PROD"
        ;;
    *)
        CMD="$INSTALL_CMD $PKGS_BASE"
        ;;
esac

echo $CMD
$CMD

if [[ $? != 0 ]]; then
    echo 'Setup failed.' >&2
    exit 1
fi

echo
echo "Checking Docker prerequisites..."

if ! command -v docker >/dev/null; then
    echo 'I cannot find a `docker` executable in your PATH. Please make sure' >&2
    echo 'you have installed Docker as described in docs/installation_notes.md.' >&2
    exit 1
fi

if ! grep -q swapaccount=1 /proc/cmdline; then
    echo 'Swap accounting seems to be disabled. Please make sure you have' >&2
    echo 'configured GRUB as described in docs/installation_notes.md.' >&2
    exit 1
fi

echo "Done! Your system appears to be configured correctly."
