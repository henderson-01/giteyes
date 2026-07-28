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
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_data", "Refresh"),
    ]

    def __init__(self, source: DataSource, weeks: int = 13, **kwargs) -> None:
        super().__init__(**kwargs)
        self.source = source
        self.weeks = weeks

    def compose(self) -> ComposeResult:
        # The Header is the built-in Textual bar at the very top of the app.
        # Setting show_clock=True displays the current time on the right side.
        yield Header(show_clock=True)

        # 'body' is our main wrapper container. The Vertical layout means
        # everything inside it will be stacked from top to bottom.
        with Vertical(id="body"):

            # TOP SECTION.
            # This Vertical container spans the top half of the body.
            # In the TCSS, this gets a nice rounded border and '1fr' height.
            with Vertical(id="top-panel"):
                # 'Static' renders plain text, which we use as a section title here.
                yield Static("recent commits", classes="section-title")
                # The widget that displays the list of commits, taking up the rest of the panel.
                yield CommitTable(id="commits")

            # BOTTOM SECTION.
            # A Horizontal container places everything inside it side-by-side (left-to-right).
            # This splits the lower half of the screen into columns.
            with Horizontal(id="panels"):

                # LEFT COLUMN.
                # This vertical container takes up the left side of the bottom section.
                # In the TCSS gives it '2fr' width, meaning it takes up 2/3 of the horizontal space.
                with Vertical(id="left-panel"):
                    yield Static("churn hotspots", classes="section-title")
                    # The widget displaying the bars for frequently changed files.
                    yield HotspotBars([], id="hotspots")

                # RIGHT COLUMN.
                # This vertical container takes up the right side of the bottom section.
                # In the TCSS gives it '1fr' width, meaning it takes up 1/3 of the horizontal space.
                with Vertical(id="right-panel"):
                    yield Static("commit activity", classes="section-title")
                    # The widget showing the grid/heatmap of activity over time.
                    yield CommitHeatmap([], id="heatmap")

                    yield Static("contributors", classes="section-title")
                    # The widget showing the list of people who have contributed.
                    yield ContributorList([], id="contributors")

        # The Footer is the built-in bar at the very bottom of the app.
        # It automatically displays the BINDINGS (like "q" to Quit, "r" to Refresh).
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
        except Exception as exc:  # keep transient API/network hiccups from crashing the app
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
