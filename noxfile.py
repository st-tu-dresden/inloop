"""
Nox sessions, which each run in an isolated Python environment with
minimal dependencies. This ensures that we never accidentally depend
on dev dependencies in production code (thus, we achieve a feature
similar to Maven's dependency scopes).

The sessions are primarily used in our .travis-ci.yml.
"""

from tempfile import NamedTemporaryFile
from typing import Any

import nox
from nox.sessions import Session


def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
    """Install packages constrained by poetry's lockfile."""
    with NamedTemporaryFile() as requirements:
        # This approach is by Claudio Jolowicz, see his excellect
        # example at github.com/cjolowicz/hypermodern-python.
        session.run(
            "poetry",
            "export",
            "--dev",
            "--without-hashes",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


def build_docker_image(session: Session) -> None:
    """Build the image required by our docker integration tests."""
    session.run(
        "docker",
        "build",
        "--tag",
        "inloop-integration-test",
        "tests/testrunner",
        external=True,
    )


def poetry_install(session: Session) -> None:
    """Install the runtime dependencies with poetry."""
    session.run("poetry", "install", "--no-dev", external=True)


@nox.session(python=["3.7", "3.8"])
def tests(session: Session) -> None:
    """Run the complete test suite without dev dependencies."""
    args = session.posargs or ["-v2", "--failfast"]
    build_docker_image(session)
    poetry_install(session)
    install_with_constraints(session, "coverage[toml]")
    session.run("coverage", "run", "./runtests.py", "--", *args)
    session.run("coverage", "report")


@nox.session(python=["3.7"])
def lint(session: Session) -> None:
    """Check code style with flake8 and isort."""
    locations = "inloop", "tests", "noxfile.py", "manage.py", "runtests.py"
    install_with_constraints(
        session,
        "flake8",
        "flake8-annotations",
        "flake8-black",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-isort",
    )
    session.run("flake8", *locations)


@nox.session(python=["3.7"])
def pytype(session: Session) -> None:
    """Statically check for type errors with pytype."""
    args = session.posargs or ["--config", "pytype.cfg"]
    poetry_install(session)
    install_with_constraints(session, "pytype")
    session.run("pytype", *args)


@nox.session(python=["3.7"])
def typeguard(session: Session) -> None:
    """Run the test suite with run-time type checking of PEP-484 annotations."""
    args = session.posargs or ["-v2", "--failfast"]
    build_docker_image(session)
    poetry_install(session)
    install_with_constraints(session, "typeguard")
    session.run("python", "runtests.py", "--with-typeguard", "--", *args)
