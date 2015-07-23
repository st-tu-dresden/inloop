## Getting started

This file contains instructions to quickly set up a developer environment.
Please also have a look at the documentation provided for

* [contributors](docs/HACKING.md) and
* [administrators](docs/DEPLOY.md).

### Prerequisites

INLOOP is designed to exclusively run on Python 3.x. At a minimum, you need:

* Python packages: `pip`, `virtualenv`
* `gcc` or `clang` and associated build tools (`make` etc.) and header files
  for `libjpeg` and `zlib`. They are required to build and install the python
  packages `Pillow` and optionally `psycopg2`. On Ubuntu, you can satisfy this
  requirement with

    ```bash
    apt-get install build-essential python3-dev libjpeg-dev zlib1g-dev
    ```

### Developer setup

1. Clone the repository:

    ```
    git clone https://github.com/st-tu-dresden/inloop.git
    cd inloop
    ```

2. Set up a new virtualenv and install the required packages:

    ```
    virtualenv --python=python3 venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. Set up the database and super user:

    ```
    ./manage.py migrate
    ./manage.py createsuperuser
    ```

4. Run the application:

    ```
    ./manage.py runserver
    ```
