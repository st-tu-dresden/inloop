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

exitcode=0

echo $CMD
$CMD

if [[ $? != 0 ]]; then
    echo 'ERROR: Installation of packages failed.' >&2
    exitcode=1
fi

echo
echo "Checking your system setup ..."
echo

if ! command -v docker >/dev/null; then
    echo 'ERROR: I cannot find a `docker` executable in your PATH. Please make' >&2
    echo 'sure you have installed Docker as described in docs/docker_setup.md.' >&2
    exitcode=1
fi

if ! groups | grep -qw docker; then
    echo "WARNING: your account ($USER) is not part of the 'docker' group." >&2
    echo "However, you'll need this for a local developer setup." >&2
    echo "Please run 'sudo adduser $USER docker', logout and login again (or" >&2
    echo "restart your computer) to be able to use docker as a non-root user." >&2
    exitcode=1
fi

if ! command -v watchexec >/dev/null; then
    echo 'WARNING: I cannot find a `watchexec` binary in your PATH. However,' >&2
    echo "you'll need it for a local developer setup. Please install it" >&2
    echo 'manually as described on https://github.com/watchexec/watchexec.' >&2
    exitcode=1
fi

if ! grep -q swapaccount=1 /proc/cmdline; then
    echo 'ERROR: Swap accounting seems to be disabled. Please make sure you' >&2
    echo 'have configured GRUB as described in docs/docker_setup.md.' >&2
    exitcode=1
fi

if [[ $exitcode != 0 ]]; then
    echo
    echo "There have been errors and/or warnings during setup, please review the" >&2
    echo "above messages and fix the issues. After fixing the issues, run this" >&2
    echo "script again to check your setup." >&2
else
    echo
    echo "Nice! Your setup appears to be fine."
fi

exit $exitcode
