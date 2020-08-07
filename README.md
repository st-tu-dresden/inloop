
        ___       ___       ___     ___       ___       ___
       /\  \     /\__\     /\__\   /\  \     /\  \     /\  \
      _\:\  \   /:| _|_   /:/  /  /::\  \   /::\  \   /::\  \
     /\/::\__\ /::|/\__\ /:/__/  /:/\:\__\ /:/\:\__\ /::\:\__\
     \::/\/__/ \/|::/  / \:\  \  \:\/:/  / \:\/:/  / \/\::/  /
      \:\__\     |:/  /   \:\__\  \::/  /   \::/  /     \/__/
       \/__/     \/__/     \/__/   \/__/     \/__/


[![Build Status](https://travis-ci.org/st-tu-dresden/inloop.svg?branch=master)](https://travis-ci.org/st-tu-dresden/inloop)

INLOOP, the *INteractive Learning center for Object-Oriented Programming*, is a Python web
application to manage online programming courses, powered by Git, Django and Docker:

- **Flexible**: you can write tasks for arbitrary programming languages, as long as they can be
  packaged into a Docker image.
- **Secure**: solutions are checked inside a minimal and strictly isolated Docker container, which
  is discarded after execution.
- **Modern**: push-based (or periodic pull-based) import of tasks, Markdown task descriptions and
  accompanying material from a Git repository.
- **Fast & scalable**: solutions are processed asynchronously by a configurable number of
  background workers.
- **Easy to extend**: modern, modular and PEP-8 compliant Python 3 code base with less than 3000
  lines of code, good test coverage and continuous integration tests.


## Quick start

INLOOP requires the following software:

* Debian 10+ or Ubuntu 20.04+, macOS 10.13+ (for development only)
* Python 3.7 or 3.8
* Docker 19.03+ ([Docker setup](docs/docker_setup.md) **!!!**)
* Redis 5.0+
* Git 2.20+ ([workarounds for older Git versions](docs/git_troubleshouting.md))
* PostgreSQL 11+

Using the command line, a development instance can be set up as follows:

1. If you don't have it already, install [poetry](https://python-poetry.org/docs/#installation).
   If you run into trouble, the known "good" versions of the build tools are listed in
   [build-requirements.txt](build-requirements.txt).

2. Install required software with `./support/scripts/debian_setup.sh` (Debian/Ubuntu) or
   `./support/scripts/macos_setup.sh` (macOS).

3. On macOS, please run:

           export CFLAGS="-I$(brew --prefix openssl@1.1)/include $CFLAGS"
           export LDFLAGS="-L$(brew --prefix openssl@1.1)/lib $LDFLAGS"

   (This is necessary on Python 3.7 or newer to build the `psycopg2` library.)

4. Run `make init` and `make loaddb` to bootstrap your local development environment.

5. Start and monitor the development web server and huey workers with `make run`.

6. The previous step prints the address and port number of the local webserver that was started.
   You can immediately log in using the demo user accounts *admin*, *staff*, and *student* with
   the password *secret*.

You can use our [Java example task repository][repo-example] as a starting point to explore INLOOP.

[repo-example]: https://github.com/st-tu-dresden/inloop-java-repository-example

## Demo

[![INLOOP demo on YouTube](docs/figures/video.jpg)](https://youtu.be/cZ_fGQzL5Sw)


## Documentation

* [Task repository manual](docs/task_repository_manual.md)
* [Installation/deployment manual](docs/INSTALL.md)
* [Contributor guide](CONTRIBUTING.md)


## Publications

* M. Morgenstern and B. Demuth: [Continuous Publishing of Online Programming Assignments with
  INLOOP][isee18pdf] (ISEE 2018: 1st Workshop on Innovative Software Engineering Education).

[isee18pdf]: http://ceur-ws.org/Vol-2066/isee2018paper08.pdf


## Authors and credits

**Project lead**: Martin Morgenstern<br>
**Contributors**: Dominik Muhs, Philipp Matthes, Julian Catoni

INLOOP borrows its concept from the Praktomat, developed originally at the
University of Passau and later at the Karlsruhe Institute of Technology:

* http://pp.ipd.kit.edu/projects/praktomat/praktomat.php
* https://github.com/KITPraktomatTeam/Praktomat


## License

INLOOP is released under GPL version 3.

    Copyright (C) 2015-2017 Dominik Muhs and Martin Morgenstern
    Copyright (C) 2018-2020 Philipp Matthes and Martin Morgenstern
    Economic rights: Technische Universität Dresden (Germany)

    INLOOP is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    INLOOP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
