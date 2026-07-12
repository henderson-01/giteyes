from __future__ import annotations

from typer.testing import CliRunner

from giteyes.cli import app

runner = CliRunner()


def test_version_flag_prints_version_and_exits():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "giteyes" in result.stdout


def test_rejects_non_git_directory(tmp_path):
    result = runner.invoke(app, [str(tmp_path)])
    assert result.exit_code == 1
    assert "not a git repository" in result.stdout


def test_target_missing_on_disk_routes_to_github_source(monkeypatch, tmp_path):
    # Run from an empty tmp dir so "octocat/Hello-World" can't resolve to a real local path.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("giteyes.cli.GitHubApiSource.verify_repo_exists", lambda self: None)
    monkeypatch.setattr("giteyes.cli.GiteyesApp.run", lambda self: None)

    result = runner.invoke(app, ["octocat/Hello-World"])
    assert result.exit_code == 0
