## Hacking

### Unit tests and test coverage

Developers should write unit tests in order to ensure software quality in
an automated fashion. Python and Django provide excellent modules which
facilitate testing:

 * `unittest`,
 * `unittest.mock` (Python >= 3.3) and
 * `django.utils.unittest`

The test coverage can be checked by using

    ./coverage.py

and pointing your browser to `htmlcov/index.html`. Aim for 100%!


### Automatic code checking git hook with flake8

It is mandatory for all developers to implement this pre-commit hook mechanism to
check their code before every commit. In case the `flake8` check throws any errors,
the committing process is canceled and the errors are shown for correction. The
bundled commit hook can be installed as follows:

    cd .git/hooks
    ln -sf ../../support/pre-commit.sh pre-commit


### Commit message git hook

You must also install the commit message hook to enforce consistent commit messages:

    cd .git/hooks
    ln -s ../../support/commit_msg.py commit-msg


### Notes on flake8

We use [flake8][1] for linting. It implements wrappers for [pep8][2], the [pyflakes][3]
linter and [mccabe][4]. The parameters for the hook are contained in `setup.cfg` in the
project root.

The pre-defined command `flake8 --install-hook` is also a  means of installing the
pre-commit hook as it is now, but allows less customization and more importantly lacks
support for virtualenv in IDEs. The mechanism works when executed from the shell but
most IDEs can't execute the git hooks within their virtualenv.

[1]: http://flake8.readthedocs.org/en/latest/index.html
[2]: https://pypi.python.org/pypi/pep8
[3]: https://pypi.python.org/pypi/pyflakes
[4]: https://pypi.python.org/pypi/mccabe
