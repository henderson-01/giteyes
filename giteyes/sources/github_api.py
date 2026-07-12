"""DataSource backed by the GitHub REST API — no clone required.

This trades completeness for zero setup. In particular:
  - Unauthenticated requests are capped at 60/hour by GitHub. Pass a token
    (via --token or the GITHUB_TOKEN env var) to raise that to 5,000/hour.
  - The heatmap deliberately avoids GitHub's `/stats/commit_activity`
    endpoint. That endpoint is computed asynchronously and cached — for a
    repo GitHub hasn't been asked about recently, it returns 202 while it
    computes in the background, and can stay that way for a while. Instead,
    the heatmap counts commits directly from the standard (synchronous,
    always-reliable) commits-listing endpoint, using the exact same
    grid-building logic as local mode.
  - There's no cheap API for "which files churn the most" across full
    history. Rather than pay for that with dozens of extra requests, churn
    hotspots here are derived from the same recent commits already fetched
    for the commit table — a smaller, honest window rather than a slow,
    rate-limit-hungry approximation of the local mode's behavior.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone

import requests

from .. import git_data
from ..models import CommitInfo, ContributorInfo, FileChurn

API_ROOT = "https://api.github.com"

# Accepts: https://github.com/owner/repo, github.com/owner/repo,
# git@github.com:owner/repo.git, and the bare "owner/repo" shorthand.
_GITHUB_PATTERNS = [
    re.compile(r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$"),
    re.compile(r"^github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$"),
    re.compile(r"^git@github\.com:(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?$"),
    re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)$"),
]


def parse_github_spec(text: str) -> tuple[str, str] | None:
    """Return (owner, repo) if `text` looks like a GitHub repo reference, else None."""
    text = text.strip()
    for pattern in _GITHUB_PATTERNS:
        match = pattern.match(text)
        if match:
            return match.group("owner"), match.group("repo")
    return None


class GitHubApiError(Exception):
    """Raised for any unrecoverable GitHub API failure (auth, rate limit, 404, ...)."""


class GitHubApiSource:
    """Pulls the dashboard's data from api.github.com for a repo you haven't cloned."""

    def __init__(self, owner: str, repo: str, token: str | None = None, session: requests.Session | None = None) -> None:
        self.owner = owner
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self._session = session or requests.Session()
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self._session.headers.update(headers)
        self._commit_cache: list[dict] | None = None

    @property
    def label(self) -> str:
        return f"{self.owner}/{self.repo} (GitHub API)"

    def _get(self, path: str, params: dict | None = None) -> requests.Response:
        response = self._session.get(f"{API_ROOT}{path}", params=params, timeout=10)
        if response.status_code == 404:
            raise GitHubApiError(f"{self.owner}/{self.repo} not found on GitHub (or it's private).")
        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(response.headers.get("X-RateLimit-Reset", 0))
            reset_str = (
                datetime.fromtimestamp(reset, tz=timezone.utc).strftime("%H:%M:%S UTC") if reset else "soon"
            )
            raise GitHubApiError(
                f"GitHub API rate limit hit, resets at {reset_str}. "
                "Set GITHUB_TOKEN (or pass --token) to raise the limit from 60 to 5,000 requests/hour."
            )
        if response.status_code >= 400:
            raise GitHubApiError(f"GitHub API error {response.status_code} for {self.owner}/{self.repo}.")
        return response

    def verify_repo_exists(self) -> None:
        """Raises GitHubApiError early if the repo doesn't exist / isn't reachable."""
        self._get(f"/repos/{self.owner}/{self.repo}")

    def get_heatmap_grid(self, weeks: int = 13) -> list[list[int]]:
        since = datetime.now(timezone.utc) - timedelta(weeks=weeks)
        counts: dict = {}
        page = 1
        while page <= 10:  # safety cap: 1,000 commits is far more than 13 weeks needs
            commits = self._get(
                f"/repos/{self.owner}/{self.repo}/commits",
                params={"since": since.isoformat(), "per_page": 100, "page": page},
            ).json()
            if not commits:
                break
            for commit in commits:
                commit_date = datetime.fromisoformat(
                    commit["commit"]["author"]["date"].replace("Z", "+00:00")
                ).date()
                counts[commit_date] = counts.get(commit_date, 0) + 1
            if len(commits) < 100:
                break
            page += 1
        return git_data.build_heatmap_grid(counts, weeks=weeks)

    def _fetch_recent_commits_raw(self, limit: int) -> list[dict]:
        if self._commit_cache is not None and len(self._commit_cache) >= limit:
            return self._commit_cache[:limit]

        summaries = self._get(f"/repos/{self.owner}/{self.repo}/commits", params={"per_page": limit}).json()
        detailed = [self._get(f"/repos/{self.owner}/{self.repo}/commits/{s['sha']}").json() for s in summaries]
        self._commit_cache = detailed
        return detailed

    def get_recent_commits(self, limit: int = 12) -> list[CommitInfo]:
        commits = []
        for detail in self._fetch_recent_commits_raw(limit):
            commit_data = detail["commit"]
            stats = detail.get("stats", {})
            author = detail.get("author") or {}
            commits.append(
                CommitInfo(
                    hexsha=detail["sha"],
                    message=commit_data["message"].strip().splitlines()[0],
                    author=author.get("login") or commit_data["author"]["name"],
                    committed_at=datetime.fromisoformat(commit_data["author"]["date"].replace("Z", "+00:00")),
                    insertions=stats.get("additions", 0),
                    deletions=stats.get("deletions", 0),
                )
            )
        return commits

    def get_contributors(self, limit: int = 8) -> list[ContributorInfo]:
        response = self._get(f"/repos/{self.owner}/{self.repo}/contributors", params={"per_page": limit})
        return [ContributorInfo(name=c["login"], email="", commit_count=c["contributions"]) for c in response.json()]

    def get_churn_hotspots(self, limit: int = 6) -> list[FileChurn]:
        changes: dict[str, int] = {}
        touches: dict[str, int] = {}
        for detail in self._fetch_recent_commits_raw(limit=20):
            for file_info in detail.get("files", []):
                path = file_info["filename"]
                changes[path] = changes.get(path, 0) + file_info.get("changes", 0)
                touches[path] = touches.get(path, 0) + 1

        ranked = sorted(changes.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return [FileChurn(path=path, changes=count, commit_count=touches[path]) for path, count in ranked]
