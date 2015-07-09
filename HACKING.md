## Hacking

### Git workflow

We use the [GitHub Flow][gh-flow]. The development is based on branching, pull requests and
peer review. You must adhere to the following rules:

1. The `master` branch always contains stable code ready to be deployed. You are only allowed
   to commit very small fixes (e.g., to correct typos) to this branch.
2. New features, bug fixes, refactorings etc. happen on separate *feature branches*. Long
   running feature branches should regularly merge changes from `master`.
3. Once a feature branch is considered complete, open a pull request and assign another
   developer for review. You are not allowed to merge the pull request yourself.

Contributors failing to follow these rules will be warned and eventually banned from the
repository.


### Unit tests and test coverage

Developers should write unit tests in order to ensure software quality in an automated fashion.
Python and Django provide excellent modules which facilitate testing:

 * `unittest`,
 * `unittest.mock` (Python >= 3.3) and
 * `django.utils.unittest`

The test coverage can be checked by using

    ./coverage.py

and pointing your browser to `htmlcov/index.html`. Aim for 100%!


### Automatic code checking git hook with flake8

It is mandatory for all developers to implement this pre-commit hook mechanism to check their
code before every commit. In case the `flake8` check throws any errors, the committing process
is canceled and the errors are shown for correction. The bundled commit hook can be installed
as follows:

    cd .git/hooks
    ln -sf ../../support/pre-commit.sh pre-commit


### Commit message git hook

You must also install the commit message hook to enforce consistent commit messages:

    cd .git/hooks
    ln -s ../../support/commit_msg.py commit-msg


### Notes on flake8

We use [flake8 for linting][flake8]. It implements wrappers for the [pep8 style checker][pep8],
the [pyflakes linter][pyflakes] linter and [mccabe complexity checker][mccabe]. The parameters
for the hook are contained in `setup.cfg` in the project root.

The pre-defined command `flake8 --install-hook` is also a  means of installing the
pre-commit hook as it is now, but allows less customization and more importantly lacks
support for virtualenv in IDEs. The mechanism works when executed from the shell but
most IDEs can't execute the git hooks within their virtualenv.

[flake8]: http://flake8.readthedocs.org/en/latest/index.html
[pep8]: https://pypi.python.org/pypi/pep8
[pyflakes]: https://pypi.python.org/pypi/pyflakes
[mccabe]: https://pypi.python.org/pypi/mccabe
[gh-flow]: https://guides.github.com/introduction/flow/
