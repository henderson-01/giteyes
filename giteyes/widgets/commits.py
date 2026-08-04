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

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        row_data = self.get_row(event.row_key)
        commit_hash = row_data[0]

        # Directly access the app and update the hotspots panel (no class import needed)
        hotspots_widget = self.app.query_one("#hotspots")
        hotspots_widget.hotspots = self.app.source.get_hotspots_for_commit(commit_hash)
        hotspots_widget.refresh()
