"""Horizontal bars showing which files change the most."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from ..models import FileChurn

MAX_PATH_WIDTH = 22
MIN_PATH_WIDTH = 8
MIN_BAR_WIDTH = 3


class HotspotBars(Static):
    """Renders a ranked list of files as horizontal churn bars.

    Bar length and filename width are both computed from the widget's
    current rendered width, so this reflows cleanly when the terminal is
    resized instead of wrapping onto extra lines.
    """

    def __init__(self, hotspots: list[FileChurn], **kwargs) -> None:
        super().__init__(**kwargs)
        self.hotspots = hotspots

    def get_content_height(self, container, viewport, width: int) -> int:
        # The row count only depends on how much data there is, never on
        # width — pin it directly so resizing can never affect panel height,
        # even at widths narrow enough to confuse Rich's own measurement.
        return len(self.hotspots) + 1 if self.hotspots else 1

    def render(self) -> Text:
        if not self.hotspots:
            return Text("no data in range", style="dim")

        max_changes = max((h.changes for h in self.hotspots), default=0)
        count_width = max((len(str(h.changes)) for h in self.hotspots), default=1)

        # Reserve room for a leading path column and a trailing " <count>",
        # then split whatever's left between the filename and the bar.
        min_total = MIN_PATH_WIDTH + MIN_BAR_WIDTH + count_width + 1
        available = max(self.size.width, min_total)
        remaining = available - count_width - 1  # -1 for the space before the count
        path_width = max(min(MAX_PATH_WIDTH, remaining // 2), MIN_PATH_WIDTH)
        bar_width = max(remaining - path_width, MIN_BAR_WIDTH)

        text = Text(no_wrap=True, overflow="ellipsis")
        for hotspot in self.hotspots:
            path = hotspot.path
            if len(path) > path_width:
                path = "…" + path[-(path_width - 1):]  # keep the filename end, it's the useful part
            bar_len = int((hotspot.changes / max_changes) * bar_width) if max_changes else 0
            text.append(f"{path:<{path_width}}", style="bold")
            text.append("█" * bar_len, style="#d85a30")
            text.append(f" {hotspot.changes}\n", style="dim")
        return text
