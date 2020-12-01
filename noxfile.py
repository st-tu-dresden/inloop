"""
Nox sessions, which each run in an isolated Python environment with
minimal dependencies. This ensures that we never accidentally depend
on dev dependencies in production code (thus, we achieve a feature
similar to Maven's dependency scopes).

The sessions are primarily used in our .travis-ci.yml.
"""

from tempfile import NamedTemporaryFile

import nox


def install_with_constraints(session, *args, **kwargs):
    """Install packages constrained by poetry's lockfile."""
    with NamedTemporaryFile() as requirements:
        # This approach is by Claudio Jolowicz, see his excellect
        # example at github.com/cjolowicz/hypermodern-python.
        session.run(
            'poetry',
            'export',
            '--dev',
            '--without-hashes',
            '--format=requirements.txt',
            f'--output={requirements.name}',
            external=True
        )
        session.install(f'--constraint={requirements.name}', *args, **kwargs)


@nox.session(python=['3.7', '3.8'])
def tests(session):
    """Run the complete test suite without dev dependencies."""
    args = session.posargs or ['-v2', '--failfast']
    session.run(
        'docker',
        'build',
        '--tag',
        'inloop-integration-test',
        'tests/testrunner',
        external=True,
    )
    session.run('poetry', 'install', '--no-dev', external=True)
    install_with_constraints(session, 'coverage')
    session.run('coverage', 'run', './manage.py', 'test', *args)
    session.run('coverage', 'report')


@nox.session(python=['3.7'])
def lint(session):
    """Check code style with flake8 and isort."""
    locations = 'inloop', 'tests', 'noxfile.py', 'manage.py'
    install_with_constraints(session, 'flake8', 'flake8-docstrings', 'isort')
    session.run(
        'isort',
        '--check-only',
        '--diff',
        '--quiet',
        *locations,
    )
    session.run('flake8', *locations)
