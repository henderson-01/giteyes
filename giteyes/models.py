"""Plain data containers shared between the git data layer and the UI widgets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CommitInfo:
    """A single commit, trimmed to what the dashboard displays."""

    hexsha: str
    message: str
    author: str
    committed_at: datetime
    insertions: int
    deletions: int

    @property
    def short_hash(self) -> str:
        return self.hexsha[:7]


@dataclass(frozen=True)
class ContributorInfo:
    """A contributor and how many commits they have in the analyzed window."""

    name: str
    email: str
    commit_count: int


@dataclass(frozen=True)
class FileChurn:
    """A file and how much it has changed in the analyzed window."""

    path: str
    changes: int
    commit_count: int
