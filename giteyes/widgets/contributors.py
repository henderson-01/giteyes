"""A simple ranked list of contributors by commit count."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from ..models import ContributorInfo

MAX_NAME_WIDTH = 20
MIN_NAME_WIDTH = 6


class ContributorList(Static):
    """Renders contributors ranked by how many commits they have.

    Name column width adapts to the widget's current rendered width, so a
    long name truncates with an ellipsis instead of wrapping onto a new line.
    """

    def __init__(self, contributors: list[ContributorInfo], **kwargs) -> None:
        super().__init__(**kwargs)
        self.contributors = contributors

    def get_content_height(self, container, viewport, width: int) -> int:
        return len(self.contributors) + 1 if self.contributors else 1

    def render(self) -> Text:
        if not self.contributors:
            return Text("no data in range", style="dim")

        suffix_width = max((len(f"{c.commit_count} commits") for c in self.contributors), default=8)
        available = max(self.size.width, MIN_NAME_WIDTH + suffix_width)
        name_width = max(min(MAX_NAME_WIDTH, available - suffix_width), MIN_NAME_WIDTH)

        text = Text(no_wrap=True, overflow="ellipsis")
        for contributor in self.contributors:
            name = contributor.name
            if len(name) > name_width:
                name = name[: name_width - 1] + "…"
            text.append(f"{name:<{name_width}}", style="#79c0ff")
            text.append(f"{contributor.commit_count} commits\n", style="dim")
        return text
