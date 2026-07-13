"""Regression tests for the terminal-resize bug: the hotspots and
contributors panels used to wrap onto extra lines (and grow taller) when the
terminal was narrowed, because their rendered text had a fixed width that
ignored the widget's actual available space.
"""

from __future__ import annotations

import pytest

from giteyes.app import GiteyesApp
from giteyes.models import ContributorInfo, FileChurn
from giteyes.sources.local import LocalGitSource
from giteyes.widgets.contributors import ContributorList
from giteyes.widgets.heatmap import CommitHeatmap
from giteyes.widgets.hotspots import HotspotBars

WIDTHS_TO_CHECK = (120, 80, 60, 40, 25, 15)


@pytest.mark.asyncio
async def test_hotspots_height_is_stable_across_terminal_widths(git_repo):
    app = GiteyesApp(source=LocalGitSource(git_repo), weeks=4)
    async with app.run_test(size=(120, 40)) as pilot:
        hotspots = app.query_one("#hotspots", HotspotBars)
        hotspots.hotspots = [
            FileChurn(path="some/very/long/nested/path/to/a/file.py", changes=176, commit_count=5),
            FileChurn(path="README.md", changes=57, commit_count=3),
        ]
        hotspots.refresh()
        await pilot.pause()

        heights = set()
        for width in WIDTHS_TO_CHECK:
            await pilot.resize_terminal(width, 40)
            await pilot.pause()
            heights.add(hotspots.size.height)

        assert heights == {3}  # 2 data rows + 1 trailing blank line, always


@pytest.mark.asyncio
async def test_contributors_height_is_stable_across_terminal_widths(git_repo):
    app = GiteyesApp(source=LocalGitSource(git_repo), weeks=4)
    async with app.run_test(size=(120, 40)) as pilot:
        contributors = app.query_one("#contributors", ContributorList)
        contributors.contributors = [
            ContributorInfo(name="a-very-long-contributor-username", email="", commit_count=42)
        ]
        contributors.refresh()
        await pilot.pause()

        heights = set()
        for width in WIDTHS_TO_CHECK:
            await pilot.resize_terminal(width, 40)
            await pilot.pause()
            heights.add(contributors.size.height)

        assert heights == {2}  # 1 data row + 1 trailing blank line, always


@pytest.mark.asyncio
async def test_heatmap_height_is_stable_across_terminal_widths(git_repo):
    app = GiteyesApp(source=LocalGitSource(git_repo), weeks=13)
    async with app.run_test(size=(120, 40)) as pilot:
        heatmap = app.query_one("#heatmap", CommitHeatmap)

        heights = set()
        for width in WIDTHS_TO_CHECK:
            await pilot.resize_terminal(width, 40)
            await pilot.pause()
            heights.add(heatmap.size.height)

        assert heights == {7}  # one row per weekday, always
