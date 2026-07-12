"""Command-line entrypoint: `giteyes [PATH-OR-GITHUB-REPO]`."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Optional

import typer

from . import git_data
from .app import GiteyesApp
from .sources.github_api import GitHubApiError, GitHubApiSource, parse_github_spec
from .sources.local import LocalGitSource

app = typer.Typer(add_completion=False, help="A terminal dashboard for git activity.")


def _version_callback(show_version: bool) -> None:
    if not show_version:
        return
    try:
        current_version = version("giteyes")
    except PackageNotFoundError:
        current_version = "0.0.0-dev"
    typer.echo(f"giteyes {current_version}")
    raise typer.Exit()


@app.command()
def main(
    target: str = typer.Argument(
        ".",
        help="A local path, or a GitHub repo (owner/repo, a github.com URL, or a git@ URL).",
    ),
    weeks: int = typer.Option(13, "--weeks", "-w", help="Weeks of history shown in the heatmap."),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        envvar="GITHUB_TOKEN",
        help="GitHub token for the GitHub API mode (raises the rate limit from 60 to 5,000/hour).",
    ),
    version_: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Launch the Giteyes dashboard for a local repo or a GitHub repo reference.

    Local paths are checked first, so a directory named e.g. "octocat/hello"
    is never mistaken for a GitHub reference — only strings that don't exist
    on disk are parsed as owner/repo.
    """
    local_path = Path(target)
    github_spec = None if local_path.exists() else parse_github_spec(target)

    if github_spec:
        owner, repo = github_spec
        source = GitHubApiSource(owner, repo, token=token)
        try:
            source.verify_repo_exists()
        except GitHubApiError as exc:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc
    else:
        try:
            source = LocalGitSource(local_path)
        except git_data.NotAGitRepoError as exc:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc

    GiteyesApp(source=source, weeks=weeks).run()


if __name__ == "__main__":
    app()
