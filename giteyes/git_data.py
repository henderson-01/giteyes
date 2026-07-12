"""Reads data out of a git repository.

Everything here takes a `git.Repo` (or a path) and returns plain data —
dicts, lists, and the dataclasses in `models.py`. Keeping this layer free of
any UI code is what makes it straightforward to unit test: build a throwaway
repo with known commits, call these functions, and assert on the result.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from .models import CommitInfo, ContributorInfo, FileChurn


class NotAGitRepoError(Exception):
    """Raised when the given path is not inside a git repository."""


def get_repo(path: Path | str) -> Repo:
    """Open the git repository containing `path`, searching parent directories."""
    try:
        return Repo(Path(path), search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError) as exc:
        raise NotAGitRepoError(f"{path} is not a git repository") from exc


def get_commit_heatmap(repo: Repo, weeks: int = 13) -> dict[date, int]:
    """Count commits per calendar day over the last `weeks` weeks."""
    since = datetime.now() - timedelta(weeks=weeks)
    counts: dict[date, int] = defaultdict(int)
    for commit in repo.iter_commits(since=since.isoformat()):
        counts[commit.committed_datetime.date()] += 1
    return dict(counts)


def build_heatmap_grid(counts: dict[date, int], weeks: int = 13) -> list[list[int]]:
    """Turn a date->count mapping into a `weeks` x 7 grid ready to render.

    Each inner list is one week, oldest first, with 7 day-slots (Mon..Sun).
    Days with no recorded commits are 0. This is separated from
    `get_commit_heatmap` so the grid-shaping logic can be tested without a
    real repository.
    """
    today = date.today()
    start = today - timedelta(days=today.weekday())  # most recent Monday
    grid: list[list[int]] = []
    for week_index in range(weeks - 1, -1, -1):
        week_start = start - timedelta(weeks=week_index)
        week = [counts.get(week_start + timedelta(days=day), 0) for day in range(7)]
        grid.append(week)
    return grid


def get_recent_commits(repo: Repo, limit: int = 12) -> list[CommitInfo]:
    """Return the `limit` most recent commits, newest first."""
    commits = []
    for commit in repo.iter_commits(max_count=limit):
        stats = commit.stats.total
        commits.append(
            CommitInfo(
                hexsha=commit.hexsha,
                message=commit.message.strip().splitlines()[0] if commit.message.strip() else "",
                author=commit.author.name or "unknown",
                committed_at=commit.committed_datetime,
                insertions=stats.get("insertions", 0),
                deletions=stats.get("deletions", 0),
            )
        )
    return commits


def get_contributors(repo: Repo, limit: int | None = None, max_commits: int = 1000) -> list[ContributorInfo]:
    """Rank contributors by commit count over the last `max_commits` commits."""
    counter: Counter[tuple[str, str]] = Counter()
    for commit in repo.iter_commits(max_count=max_commits):
        key = (commit.author.name or "unknown", commit.author.email or "")
        counter[key] += 1

    ranked = [
        ContributorInfo(name=name, email=email, commit_count=count)
        for (name, email), count in counter.most_common(limit)
    ]
    return ranked


def get_churn_hotspots(repo: Repo, limit: int = 6, max_commits: int = 200) -> list[FileChurn]:
    """Rank files by total lines changed over the last `max_commits` commits."""
    changes: Counter[str] = Counter()
    touches: Counter[str] = Counter()
    for commit in repo.iter_commits(max_count=max_commits):
        for path, stat in commit.stats.files.items():
            changes[path] += stat.get("lines", 0)
            touches[path] += 1

    hotspots = [
        FileChurn(path=path, changes=count, commit_count=touches[path])
        for path, count in changes.most_common(limit)
    ]
    return hotspots
