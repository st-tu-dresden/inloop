import nox


@nox.session(python=['3.6', '3.7'])
def tests(session):
    """Run the complete test suite without dev dependencies."""
    session.run('poetry', 'install', '--no-dev', external=True)
    session.run('python', 'manage.py', 'test', '-v2')
