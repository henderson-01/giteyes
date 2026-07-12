from __future__ import annotations

import pytest

from giteyes import git_data


def test_get_repo_reads_existing_repo(git_repo):
    repo = git_data.get_repo(git_repo)
    assert not repo.bare


def test_get_repo_rejects_non_git_directory(tmp_path):
    with pytest.raises(git_data.NotAGitRepoError):
        git_data.get_repo(tmp_path)


def test_get_recent_commits_returns_newest_first(git_repo):
    repo = git_data.get_repo(git_repo)
    commits = git_data.get_recent_commits(repo, limit=10)
    messages = [c.message for c in commits]
    assert messages[0] == "fix bug"
    assert messages[-1] == "initial commit"


def test_get_recent_commits_tracks_line_changes(git_repo):
    repo = git_data.get_repo(git_repo)
    commits = git_data.get_recent_commits(repo, limit=10)
    add_feature = next(c for c in commits if c.message == "add feature")
    assert add_feature.insertions == 2


def test_commit_heatmap_counts_one_entry_per_commit(git_repo):
    repo = git_data.get_repo(git_repo)
    counts = git_data.get_commit_heatmap(repo, weeks=3)
    assert sum(counts.values()) == 4


def test_build_heatmap_grid_has_expected_shape():
    grid = git_data.build_heatmap_grid({}, weeks=5)
    assert len(grid) == 5
    assert all(len(week) == 7 for week in grid)


def test_get_contributors_counts_commits_per_author(git_repo):
    repo = git_data.get_repo(git_repo)
    contributors = git_data.get_contributors(repo)
    assert contributors[0].name == "Test User"
    assert contributors[0].commit_count == 4


def test_get_churn_hotspots_ranks_most_changed_file_first(git_repo):
    repo = git_data.get_repo(git_repo)
    hotspots = git_data.get_churn_hotspots(repo, limit=5)
    assert hotspots[0].path == "app.py"
    assert {h.path for h in hotspots} == {"app.py", "utils.py"}
