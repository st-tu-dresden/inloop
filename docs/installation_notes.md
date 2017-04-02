Installation notes
==================

## Docker setup

### Mac OS X

Install Docker for Mac as described on https://docs.docker.com/docker-for-mac/.


## Ubuntu/Debian

The `docker.io` package shipped with Ubuntu and Debian is usually too old. Install from the Docker
APT repositories instead:

* Ubuntu: https://docs.docker.com/engine/installation/linux/ubuntulinux/
* Debian: https://docs.docker.com/engine/installation/linux/debian/

INLOOP depends on the `--memory` option to limit memory available to a container.  If you have
followed the linked installation docs carefully, running

    grep -o swapaccount=1 /proc/cmdline

should print

    swapaccount=1

If not, you need to add `cgroup_enable=memory swapaccount=1` to your `GRUB_CMDLINE_LINUX` (usually
in `/etc/default/grub`), run `update-grub` and reboot (see the linked Docker docs for details).
