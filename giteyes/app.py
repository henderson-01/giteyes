"""The Giteyes Textual application: a single-screen git activity dashboard."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from .sources import DataSource
from .widgets.commits import CommitTable
from .widgets.contributors import ContributorList
from .widgets.heatmap import CommitHeatmap
from .widgets.hotspots import HotspotBars


class GiteyesApp(App):
    """A terminal dashboard summarizing activity in a git repository.

    Works the same whether `source` is a local repo on disk or the GitHub
    API — the app only ever talks to the DataSource interface.
    """

    CSS_PATH = "app.tcss"
    BINDINGS = [  # noqa: RUF012
        ("q", "quit", "Quit"),
        ("r", "refresh_data", "Refresh"),
    ]

    def __init__(self, source: DataSource, weeks: int = 13, **kwargs) -> None:
        super().__init__(**kwargs)
        self.source = source
        self.weeks = weeks

    def compose(self) -> ComposeResult:
        # Built-in top bar; show_clock adds the time on the right.
        yield Header(show_clock=True)

        # Main wrapper, stacking its children top to bottom.
        with Vertical(id="body"):
            # Top: recent commits.
            with Vertical(id="top-panel"):
                yield Static("recent commits", classes="section-title")
                yield CommitTable(id="commits")

            # Bottom: two columns side by side.
            with Horizontal(id="panels"):
                # Left column (2fr): churn hotspots.
                with Vertical(id="left-panel"):
                    yield Static("churn hotspots", classes="section-title")
                    yield HotspotBars([], id="hotspots")

                # Right column (1fr): activity heatmap and contributors.
                with Vertical(id="right-panel"):
                    yield Static("commit activity", classes="section-title")
                    yield CommitHeatmap([], id="heatmap")

                    yield Static("contributors", classes="section-title")
                    yield ContributorList([], id="contributors")

        # Built-in bottom bar; shows BINDINGS.
        yield Footer()

    def on_mount(self) -> None:
        self.title = "giteyes"
        self.sub_title = self.source.label
        self.load_data()

    def action_refresh_data(self) -> None:
        self.load_data()

    def load_data(self) -> None:
        try:
            heatmap_grid = self.source.get_heatmap_grid(weeks=self.weeks)
            recent_commits = self.source.get_recent_commits(limit=12)
            hotspots_data = self.source.get_churn_hotspots(limit=6)
            contributors_data = self.source.get_contributors(limit=8)
        except Exception as exc:  # Keep transient API/network errors from crashing the app.  # noqa: BLE001
            self.notify(str(exc), severity="error", timeout=8)
            return

        heatmap = self.query_one("#heatmap", CommitHeatmap)
        heatmap.grid = heatmap_grid
        heatmap.refresh()

        self.query_one("#commits", CommitTable).populate(recent_commits)

        hotspots = self.query_one("#hotspots", HotspotBars)
        hotspots.hotspots = hotspots_data
        hotspots.refresh()

        contributors = self.query_one("#contributors", ContributorList)
        contributors.contributors = contributors_data
        contributors.refresh()
