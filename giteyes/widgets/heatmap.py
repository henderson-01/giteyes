"""A GitHub-style commit activity heatmap, rendered as colored blocks."""

from __future__ import annotations

from datetime import date, timedelta

from rich.text import Text
from textual import events
from textual.widgets import Static

# Five intensity buckets, lightest to darkest — matches GitHub's own palette
# so the widget reads instantly to anyone who has looked at a contributions graph.
INTENSITY_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

# Each cell renders as "■ " — a block plus a trailing space — so every
# column is 2 characters wide. Hover math below depends on this.
CELL_WIDTH = 2


def _bucket(count: int, max_count: int) -> int:
    if count <= 0 or max_count <= 0:
        return 0
    ratio = count / max_count
    if ratio > 0.75:
        return 4
    if ratio > 0.5:
        return 3
    if ratio > 0.25:
        return 2
    return 1


class CommitHeatmap(Static):
    """Renders a `weeks` x 7 grid of commit counts as colored blocks.

    Hovering a square shows a tooltip with that day's date and commit count.
    """

    def __init__(self, grid: list[list[int]], **kwargs) -> None:
        super().__init__(**kwargs)
        self.grid = grid

    def get_content_height(self, container, viewport, width: int) -> int:
        return 7 if self.grid else 1

    def render(self) -> Text:
        if not self.grid:
            return Text("no commit history in range", style="dim")

        max_count = max((count for week in self.grid for count in week), default=0)
        text = Text(no_wrap=True, overflow="ellipsis")
        for day in range(7):
            for week in self.grid:
                count = week[day] if day < len(week) else 0
                color = INTENSITY_COLORS[_bucket(count, max_count)]
                text.append("■ ", style=color)
            text.append("\n")
        return text

    def _date_for_cell(self, week_col: int, day_row: int) -> date:
        """The calendar date a given (week, day) cell represents.

        Mirrors the anchoring used to build the grid in the first place
        (git_data.build_heatmap_grid): the last column is the current week,
        and day 0 is Monday.
        """
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        weeks_back = (len(self.grid) - 1) - week_col
        week_start = this_monday - timedelta(weeks=weeks_back)
        return week_start + timedelta(days=day_row)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        week_col = int(event.x) // CELL_WIDTH
        day_row = int(event.y)

        if self.grid and 0 <= day_row < 7 and 0 <= week_col < len(self.grid):
            count = self.grid[week_col][day_row]
            cell_date = self._date_for_cell(week_col, day_row)
            commit_word = "commit" if count == 1 else "commits"
            self.tooltip = f"{cell_date:%a %d %b %Y} — {count} {commit_word}"
        else:
            self.tooltip = None

    def on_leave(self, event: events.Leave) -> None:
        self.tooltip = None
