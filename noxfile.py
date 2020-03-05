import nox


@nox.session(python=['3.6', '3.7'])
def tests(session):
    """Run the complete test suite without dev dependencies."""
    session.run('poetry', 'install', '--no-dev', external=True)
    session.run('python', 'manage.py', 'test', '-v2')


@nox.session(python=['3.6'])
def lint(session):
    """Check code style with flake8 and isort."""
    locations = 'inloop', 'tests', 'noxfile.py', 'manage.py'
    session.install('flake8', 'flake8-docstrings', 'isort')
    session.run(
        'isort',
        '--check-only',
        '--diff',
        '--quiet',
        '--recursive',
        *locations,
    )
    session.run('flake8', *locations)
