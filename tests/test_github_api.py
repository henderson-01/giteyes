from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import requests

from giteyes.sources.github_api import GitHubApiError, GitHubApiSource, parse_github_spec


@pytest.mark.parametrize(
    "text,expected",
    [
        ("octocat/Hello-World", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World.git", ("octocat", "Hello-World")),
        ("github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("git@github.com:octocat/Hello-World.git", ("octocat", "Hello-World")),
    ],
)
def test_parse_github_spec_accepts_common_formats(text, expected):
    assert parse_github_spec(text) == expected


def test_parse_github_spec_rejects_unrelated_text():
    assert parse_github_spec("this isn't a repo reference!!") is None


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None, text=""):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._json_data


def _fake_session(routes: dict[str, _FakeResponse]) -> requests.Session:
    """A real Session (for header handling) with `.get` swapped for a router.

    Routes match on URL suffix; query params are passed separately by our
    code so they never need to appear in the route key.
    """
    session = requests.Session()

    def fake_get(url, params=None, timeout=None):
        for suffix, response in routes.items():
            if url.endswith(suffix):
                return response
        raise AssertionError(f"unexpected URL requested: {url}")

    session.get = fake_get
    return session


def test_verify_repo_exists_raises_on_404():
    session = _fake_session({"/repos/octocat/missing": _FakeResponse(status_code=404)})
    source = GitHubApiSource("octocat", "missing", session=session)
    with pytest.raises(GitHubApiError, match="not found"):
        source.verify_repo_exists()


def test_rate_limit_error_message_includes_reset_hint():
    session = _fake_session(
        {
            "/repos/octocat/hello": _FakeResponse(
                status_code=403,
                headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "0"},
            )
        }
    )
    source = GitHubApiSource("octocat", "hello", session=session)
    with pytest.raises(GitHubApiError, match="rate limit"):
        source.verify_repo_exists()


def test_get_heatmap_grid_counts_commits_from_commits_endpoint():
    now = datetime.now(timezone.utc)
    commits_page = [
        {"commit": {"author": {"date": now.isoformat()}}},
        {"commit": {"author": {"date": now.isoformat()}}},
        {"commit": {"author": {"date": (now - timedelta(days=3)).isoformat()}}},
    ]
    session = _fake_session({"/commits": _FakeResponse(json_data=commits_page)})
    source = GitHubApiSource("octocat", "hello", session=session)

    grid = source.get_heatmap_grid(weeks=4)
    assert sum(sum(week) for week in grid) == 3


def test_get_heatmap_grid_handles_a_repo_with_no_commits_in_range():
    session = _fake_session({"/commits": _FakeResponse(json_data=[])})
    source = GitHubApiSource("octocat", "hello", session=session)

    grid = source.get_heatmap_grid(weeks=4)
    assert len(grid) == 4
    assert sum(sum(week) for week in grid) == 0


def test_get_recent_commits_and_hotspots_share_the_same_fetch():
    summaries = [{"sha": "abc123"}]
    detail = {
        "sha": "abc123",
        "commit": {
            "message": "fix bug\n\nlonger body",
            "author": {"name": "Ada", "date": "2026-01-01T00:00:00Z"},
        },
        "author": {"login": "ada-dev"},
        "stats": {"additions": 5, "deletions": 2},
        "files": [{"filename": "app.py", "changes": 7}],
    }
    session = _fake_session(
        {
            "/commits": _FakeResponse(json_data=summaries),
            "/commits/abc123": _FakeResponse(json_data=detail),
        }
    )
    source = GitHubApiSource("octocat", "hello", session=session)

    commits = source.get_recent_commits(limit=12)
    assert commits[0].author == "ada-dev"
    assert commits[0].message == "fix bug"
    assert commits[0].insertions == 5

    hotspots = source.get_churn_hotspots(limit=5)
    assert hotspots[0].path == "app.py"
    assert hotspots[0].changes == 7


def test_get_contributors_maps_login_and_contribution_count():
    session = _fake_session(
        {"/contributors": _FakeResponse(json_data=[{"login": "ada-dev", "contributions": 42}])}
    )
    source = GitHubApiSource("octocat", "hello", session=session)
    contributors = source.get_contributors(limit=8)
    assert contributors[0].name == "ada-dev"
    assert contributors[0].commit_count == 42
