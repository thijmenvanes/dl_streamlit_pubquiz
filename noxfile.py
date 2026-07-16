"""Nox sessions."""
import os
import shutil
import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Optional

import nox

from nox_poetry import session, Session

package = "dl_streamlit_pubquiz"
python_versions = ["3.14.5"]
nox.needs_version = ">= 2021.6.6"
nox.options.sessions = [
    "bandit",
    "check-dependencies",
    "lint",
    "docs-coverage",
    "complexity",
    "type-check",
    ]


def activate_virtualenv_in_precommit_hooks(session: Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.
    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.
    Args:
        session: The Session object.
    """
    assert session.bin is not None  # noqa: S101 # nosec

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        text = hook.read_text()
        bindir = repr(session.bin)[1:-1]  # strip quotes
        if not (
            Path("A") == Path("a") and bindir.lower() in text.lower() or bindir in text
        ):
            continue

        lines = text.splitlines()
        if not (lines[0].startswith("#!") and "python" in lines[0].lower()):
            continue

        header = dedent(
            f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """
        )

        lines.insert(1, header)
        hook.write_text("\n".join(lines))


@session(name="bandit", python=python_versions)
def bandit(session: Session) -> None:
    """Run bandit to check for vulnerabilities in code."""
    args = session.posargs or ["-r", "src"]
    session.install("flake8-bandit")
    session.run("bandit", *args)


@session(name="check-dependencies", python=python_versions)
def check_dependencies(session):
    """Check for known security vulnerabilities in dependencies."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run("poetry", "install", "--with", "dev", external=True)

        session.run(
            "poetry",
            "export",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={requirements.name}",
            external=True,
        )
        args = session.posargs
        session.run("pondl", "safety", "check", "--requirements", requirements.name, *args)


@session(name="black", python=python_versions)
def black(session: Session) -> None:
    """Run black."""
    args = session.posargs or ["-r", "src"]
    session.install("flake8-black")
    session.run("black", *args)


@session(name="lint", python=python_versions)
def lint(session: Session) -> None:
    """Run lint."""
    args = session.posargs or ["src"]
    session.install("flake8")
    session.run("flake8", *args)


@session(name="docs-coverage", python=python_versions)
def docs_coverage(session: Session) -> None:
    """Run docs coverage."""
    args = session.posargs or ["-vv", "src"]
    session.install("interrogate")
    session.run("interrogate", *args)


@session(name="complexity", python=python_versions)
def complexity(session: Session) -> None:
    """Run complexity."""
    args = session.posargs or ["--ignore", "E,P,W,F", "--max-complexity", "10", "src/"]
    session.install("flake8", "mccabe")
    session.run("flake8", *args)


@session(name="type-check", python=python_versions)
def type_check(session: Session) -> None:
    """Run type check."""
    args = session.posargs or ["src"]
    session.install("mypy")
    session.run("mypy", *args)


@session(name="test-coverage", python=python_versions)
def test_coverage(session: Session) -> None:
    """Run test coverage."""
    args = session.posargs
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("pytest", "tests", "--cov=src", *args)


@session(name="tests", python=python_versions)
def tests(session: Session) -> None:
    """Run the full test suite with pytest."""
    args = session.posargs or ["tests"]
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("pytest", *args)
