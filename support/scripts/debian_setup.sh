#!/usr/bin/env bash
INSTALL_CMD="${INSTALL_CMD:-sudo apt-get install}"
PKGS_BASE="build-essential git python3 python3-dev python3-venv redis-server libpq-dev"
PKGS_PROD="$PKGS_BASE daemontools"

case "$1" in
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
    echo 'you have installed Docker as described in docs/docker_setup.md.' >&2
    exit 1
fi

if ! groups | grep -qw docker; then
    echo "WARNING: your account ($USER) is not part of the 'docker' group." >&2
    echo "Please run 'sudo adduser $USER docker' and log in again to be able" >&2
    echo "to use docker as a non-root user." >&2
fi

if ! grep -q swapaccount=1 /proc/cmdline; then
    echo 'Swap accounting seems to be disabled. Please make sure you have' >&2
    echo 'configured GRUB as described in docs/docker_setup.md.' >&2
    exit 1
fi

echo "Done! Your system appears to be configured correctly."
