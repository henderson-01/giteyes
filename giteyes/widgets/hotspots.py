"""Horizontal bars showing which files change the most."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from ..models import FileChurn

BAR_WIDTH = 20


class HotspotBars(Static):
    """Renders a ranked list of files as horizontal churn bars."""

    def __init__(self, hotspots: list[FileChurn], **kwargs) -> None:
        super().__init__(**kwargs)
        self.hotspots = hotspots

    def render(self) -> Text:
        if not self.hotspots:
            return Text("no data in range", style="dim")

        max_changes = max((h.changes for h in self.hotspots), default=0)
        text = Text()
        for hotspot in self.hotspots:
            bar_len = int((hotspot.changes / max_changes) * BAR_WIDTH) if max_changes else 0
            text.append(f"{hotspot.path:<22}", style="bold")
            text.append("█" * bar_len, style="#d85a30")
            text.append(f" {hotspot.changes}\n", style="dim")
        return text
