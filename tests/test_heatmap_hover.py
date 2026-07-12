"""Tests for the commit heatmap's hover-to-see-date tooltip."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from giteyes.widgets.heatmap import CELL_WIDTH, CommitHeatmap


def test_date_for_cell_maps_last_column_to_current_week():
    # A 3-week grid; column 2 (the last) is this week, so day 0 (Monday)
    # of that column should be this week's Monday.
    heatmap = CommitHeatmap(grid=[[0] * 7, [0] * 7, [0] * 7])
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    assert heatmap._date_for_cell(week_col=2, day_row=0) == this_monday


def test_date_for_cell_walks_backwards_one_week_per_column():
    heatmap = CommitHeatmap(grid=[[0] * 7, [0] * 7, [0] * 7])
    newest_monday = heatmap._date_for_cell(week_col=2, day_row=0)
    previous_monday = heatmap._date_for_cell(week_col=1, day_row=0)
    assert newest_monday - previous_monday == timedelta(weeks=1)


@pytest.mark.asyncio
async def test_hovering_a_square_sets_a_tooltip_with_date_and_count():
    grid = [[0, 0, 0, 0, 0, 0, 0], [5, 0, 0, 0, 0, 0, 0]]  # week 1, Monday = 5 commits
    heatmap = CommitHeatmap(grid=grid, id="heatmap")

    from textual.app import App, ComposeResult

    class _HarnessApp(App):
        def compose(self) -> ComposeResult:
            yield heatmap

    app = _HarnessApp()
    async with app.run_test() as pilot:
        # Column 1 (second week), row 0 (Monday) -> x = 1 * CELL_WIDTH, y = 0
        await pilot.hover(heatmap, offset=(CELL_WIDTH, 0))
        assert heatmap.tooltip is not None
        assert "5 commits" in heatmap.tooltip

        expected_date = heatmap._date_for_cell(week_col=1, day_row=0)
        assert f"{expected_date:%a %d %b %Y}" in heatmap.tooltip


@pytest.mark.asyncio
async def test_hovering_a_single_commit_uses_singular_wording():
    grid = [[1, 0, 0, 0, 0, 0, 0]]
    heatmap = CommitHeatmap(grid=grid, id="heatmap")

    from textual.app import App, ComposeResult

    class _HarnessApp(App):
        def compose(self) -> ComposeResult:
            yield heatmap

    app = _HarnessApp()
    async with app.run_test() as pilot:
        await pilot.hover(heatmap, offset=(0, 0))
        assert heatmap.tooltip is not None
        assert "1 commit" in heatmap.tooltip
        assert "1 commits" not in heatmap.tooltip


@pytest.mark.asyncio
async def test_leaving_the_widget_clears_the_tooltip():
    grid = [[3, 0, 0, 0, 0, 0, 0]]
    heatmap = CommitHeatmap(grid=grid, id="heatmap")

    from textual.app import App, ComposeResult

    class _HarnessApp(App):
        def compose(self) -> ComposeResult:
            yield heatmap

    app = _HarnessApp()
    async with app.run_test() as pilot:
        await pilot.hover(heatmap, offset=(0, 0))
        assert heatmap.tooltip is not None

        heatmap.on_leave(None)
        assert heatmap.tooltip is None
