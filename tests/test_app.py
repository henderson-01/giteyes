"""Headless app tests using Textual's own test harness (no real terminal needed)."""

from __future__ import annotations

import pytest

from giteyes.app import GiteyesApp
from giteyes.sources.local import LocalGitSource
from giteyes.widgets.commits import CommitTable
from giteyes.widgets.heatmap import CommitHeatmap


@pytest.mark.asyncio
async def test_app_loads_commit_data_on_mount(git_repo):
    app = GiteyesApp(source=LocalGitSource(git_repo), weeks=4)
    async with app.run_test():
        heatmap = app.query_one("#heatmap", CommitHeatmap)
        total_in_grid = sum(sum(week) for week in heatmap.grid)
        assert total_in_grid == 4

        commits_table = app.query_one("#commits", CommitTable)
        assert commits_table.row_count == 4


@pytest.mark.asyncio
async def test_refresh_binding_reloads_data(git_repo):
    app = GiteyesApp(source=LocalGitSource(git_repo), weeks=4)
    async with app.run_test() as pilot:
        await pilot.press("r")
        commits_table = app.query_one("#commits", CommitTable)
        assert commits_table.row_count == 4
