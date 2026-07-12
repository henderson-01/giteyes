"""Shared fixtures: a real, throwaway git repo with a handful of dated commits.

Using the actual `git` binary (rather than mocking GitPython) means the tests
exercise the exact same code path as a real user's repo, at the cost of a
few milliseconds per test — a good trade for a tool whose entire job is
reading git history correctly.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest


def _run_git(repo_path: Path, *args: str, env: dict | None = None) -> None:
    subprocess.run(["git", *args], cwd=repo_path, check=True, capture_output=True, env=env)


def _commit(repo_path: Path, filename: str, content: str, message: str, when: datetime) -> None:
    (repo_path / filename).write_text(content)
    _run_git(repo_path, "add", filename)
    date_str = when.strftime("%Y-%m-%dT%H:%M:%S")
    env = {**os.environ, "GIT_AUTHOR_DATE": date_str, "GIT_COMMITTER_DATE": date_str}
    _run_git(repo_path, "commit", "-m", message, env=env)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A repo with 4 commits touching 2 files, spread over the last 10 days."""
    repo_path = tmp_path / "sample-repo"
    repo_path.mkdir()
    _run_git(repo_path, "init", "-q", "-b", "main")
    _run_git(repo_path, "config", "user.email", "test@example.com")
    _run_git(repo_path, "config", "user.name", "Test User")

    now = datetime.now()
    _commit(repo_path, "app.py", "print('v1')\n", "initial commit", now - timedelta(days=10))
    _commit(repo_path, "app.py", "print('v2')\nprint('v2b')\n", "add feature", now - timedelta(days=5))
    _commit(repo_path, "utils.py", "def helper():\n    return 1\n", "add helper", now - timedelta(days=2))
    _commit(repo_path, "app.py", "print('v3')\n", "fix bug", now)

    return repo_path
