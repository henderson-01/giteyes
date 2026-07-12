"""A simple ranked list of contributors by commit count."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from ..models import ContributorInfo


class ContributorList(Static):
    """Renders contributors ranked by how many commits they have."""

    def __init__(self, contributors: list[ContributorInfo], **kwargs) -> None:
        super().__init__(**kwargs)
        self.contributors = contributors

    def render(self) -> Text:
        if not self.contributors:
            return Text("no data in range", style="dim")

        text = Text()
        for contributor in self.contributors:
            text.append(f"{contributor.name:<20}", style="#79c0ff")
            text.append(f"{contributor.commit_count} commits\n", style="dim")
        return text
