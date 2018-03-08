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


[docker-post-install]: https://docs.docker.com/engine/installation/linux/linux-postinstall/#your-kernel-does-not-support-cgroup-swap-limit-capabilities 
