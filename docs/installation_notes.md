Installation notes
==================

Docker setup
------------

### Mac OS X

Install Docker for Mac as described on https://docs.docker.com/docker-for-mac/.


### Ubuntu/Debian

The `docker.io` package shipped with Ubuntu and Debian is usually too old. Install from the Docker
APT repositories instead:

* Ubuntu: https://docs.docker.com/engine/installation/linux/ubuntu/
* Debian: https://docs.docker.com/engine/installation/linux/debian/

**Important**: Please follow the [post-installation steps][docker-post-install] to enable swap
limit support in the kernel. INLOOP uses the `--memory` option to limit memory available to a
container. If not configured correctly, all integration tests will fail because the `docker`
command permanently prints a warning message:

> WARNING: Your kernel does not support swap limit capabilities. Limitation discarded.


Old Git versions on Debian
--------------------------

In its standard installation, Debian 8 ships with Git version 2.1. But the Git import component
of INLOOP relies on support for the `GIT_SSH_COMMAND` environment variable, which has been
introduced in Git 2.3. There are two possible workarounds for this problem:

* Option 1: Install Git from the [backports repository](https://backports.debian.org/Instructions/),
  which provides a more up-to-date version.
* Option 2: Put the following configuration options into the file `$HOME/.ssh/config`, where
  `$HOME` is the home directory of the user that runs the queue (typically `huey`):

      BatchMode yes
      StrictHostKeyChecking no


[docker-post-install]: https://docs.docker.com/engine/installation/linux/linux-postinstall/#your-kernel-does-not-support-cgroup-swap-limit-capabilities 
