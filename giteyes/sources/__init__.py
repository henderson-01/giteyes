"""Data source abstraction.

The dashboard doesn't care whether its data comes from a local `.git`
directory or the GitHub API — it just needs something that can answer these
four questions. `LocalGitSource` and `GitHubApiSource` both implement this
shape, so `app.py` and the widgets are written once and work with either.
"""

from __future__ import annotations

from typing import Protocol

from ..models import CommitInfo, ContributorInfo, FileChurn


class DataSource(Protocol):
    """Anything that can supply the dashboard's four panels of data."""

    label: str

    def get_heatmap_grid(self, weeks: int) -> list[list[int]]: ...

    def get_recent_commits(self, limit: int) -> list[CommitInfo]: ...

    def get_contributors(self, limit: int) -> list[ContributorInfo]: ...

    def get_churn_hotspots(self, limit: int) -> list[FileChurn]: ...
