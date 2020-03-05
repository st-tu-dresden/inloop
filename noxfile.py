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
            '--format=requirements.txt',
            f'--output={requirements.name}',
            external=True
        )
        session.install(f'--constraint={requirements.name}', *args, **kwargs)


@nox.session(python=['3.6', '3.7'])
def tests(session):
    """Run the complete test suite without dev dependencies."""
    args = session.posargs or ['-v2']
    session.run('poetry', 'install', '--no-dev', external=True)
    session.run('python', 'manage.py', 'test', *args)


@nox.session(python=['3.6'])
def lint(session):
    """Check code style with flake8 and isort."""
    locations = 'inloop', 'tests', 'noxfile.py', 'manage.py'
    install_with_constraints(session, 'flake8', 'flake8-docstrings', 'isort')
    session.run(
        'isort',
        '--check-only',
        '--diff',
        '--quiet',
        '--recursive',
        *locations,
    )
    session.run('flake8', *locations)
