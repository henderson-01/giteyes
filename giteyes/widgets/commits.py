"""A table of recent commits with colored insertion/deletion counts."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import DataTable

from ..models import CommitInfo


class CommitTable(DataTable):
    """A DataTable pre-configured to display `CommitInfo` rows."""

    def on_mount(self) -> None:
        self.add_columns("hash", "message", "author", "+", "-")
        self.cursor_type = "row"
        self.zebra_stripes = True

    def populate(self, commits: list[CommitInfo]) -> None:
        self.clear()
        for commit in commits:
            self.add_row(
                commit.short_hash,
                commit.message,
                commit.author,
                Text(f"+{commit.insertions}", style="#26a641"),
                Text(f"-{commit.deletions}", style="#f85149"),
            )
