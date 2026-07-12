"""DataSource backed by a local .git directory (the original behavior)."""

from __future__ import annotations

from pathlib import Path

from .. import git_data
from ..models import CommitInfo, ContributorInfo, FileChurn


class LocalGitSource:
    """Reads directly from a git repository already on disk."""

    def __init__(self, repo_path: Path | str = ".") -> None:
        self.repo_path = Path(repo_path)
        self._repo = git_data.get_repo(self.repo_path)  # raises NotAGitRepoError early

    @property
    def label(self) -> str:
        return str(self.repo_path.resolve())

    def get_heatmap_grid(self, weeks: int = 13) -> list[list[int]]:
        counts = git_data.get_commit_heatmap(self._repo, weeks=weeks)
        return git_data.build_heatmap_grid(counts, weeks=weeks)

    def get_recent_commits(self, limit: int = 12) -> list[CommitInfo]:
        return git_data.get_recent_commits(self._repo, limit=limit)

    def get_contributors(self, limit: int = 8) -> list[ContributorInfo]:
        return git_data.get_contributors(self._repo, limit=limit)

    def get_churn_hotspots(self, limit: int = 6) -> list[FileChurn]:
        return git_data.get_churn_hotspots(self._repo, limit=limit)
