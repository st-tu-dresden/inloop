        ___       ___       ___       ___       ___       ___
       /\  \     /\__\     /\__\     /\  \     /\  \     /\  \
      _\:\  \   /:| _|_   /:/  /    /::\  \   /::\  \   /::\  \
     /\/::\__\ /::|/\__\ /:/__/    /:/\:\__\ /:/\:\__\ /::\:\__\
     \::/\/__/ \/|::/  / \:\  \    \:\/:/  / \:\/:/  / \/\::/  /
      \:\__\     |:/  /   \:\__\    \::/  /   \::/  /     \/__/
       \/__/     \/__/     \/__/     \/__/     \/__/

[![License: GPL v3](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Development status: Beta](https://img.shields.io/badge/development%20status-beta-orange.svg)](#)
[![Build Status](https://travis-ci.org/st-tu-dresden/inloop.svg?branch=master)](https://travis-ci.org/st-tu-dresden/inloop)

INLOOP, the interactive learning center for object-oriented programming, is a lean web app for
online programming courses, built upon Django and Docker:

- **Flexible**: you can write tasks for arbitrary languages, as long as they can be packaged into a
  Docker image.
- **Secure**: solutions are checked inside a minimal and strictly isolated Docker container, which
  is discarded after execution.
- **Modern**: push-based (or periodic pull-based) import of tasks, Markdown task descriptions and
  accompanying attachments from a Git repository.
- **Fast & scalable**: solutions are processed asynchronously by a configurable amount of
  background workers.
- **Hackable**: modern, modular and PEP-8 compliant Python 3 code base with less than 3000 lines of
  code, good test coverage and continuous integration tests.

TEST.

## Quick start

INLOOP requires the following software:

* Debian 8+ or Ubuntu 16.04+, macOS 10.11+ (for development only)
* Python 3.4 or 3.5
* Docker 1.10+ (see the [installation notes](docs/installation_notes.md) **!!!**)
* Redis 2.6+
* Git 2.3+

Using the command line, a development instance can be set up as follows:

```bash
# 1.) install required software for Debian/Ubuntu or macOS
./support/scripts/[debian|macos]_setup.sh

# 2.) initialize a virtualenv with all required Python packages
make devenv && source .venvs/py3*/bin/activate

# 3.) start and monitor the web server and huey workers
honcho start
```

For demonstration and development purposes only, a superuser account *admin* and an ordinary user
account *student* have been created, with both passwords set to *secret*.

**Tip**: Add the line `DJDT=1` to your `.env` file to enable the Django debug toolbar.


## Further documentation

* [Deployment](docs/deployment.md)
* [Contributor guide](CONTRIBUTING.md)


## Authors and credits

**Project lead**: Martin Morgenstern<br>
**Contributors**: Dominik Muhs, Jonathan Seitz

INLOOP borrows its concept from the Praktomat, developed originally at the
University of Passau and later at the Karlsruhe Institute of Technology:

* http://pp.ipd.kit.edu/projects/praktomat/praktomat.php
* https://github.com/KITPraktomatTeam/Praktomat


## License

INLOOP is released under GPL version 3.

    Copyright (C) 2015-2017 Dominik Muhs and Martin Morgenstern
    Economic rights: Technische Universität Dresden (Germany)

    INLOOP is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    INLOOP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
