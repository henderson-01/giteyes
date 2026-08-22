## Development

Running the test suite is handled smoothly through `uv`.

First, ensure you have the development dependencies installed:

```bash
uv sync --extra dev

```

Then, run the tests:

```bash
uv run pytest

```

Tests build a real throwaway git repo with scripted, dated commits (see `tests/conftest.py`), exercising the actual code paths without touching your broader filesystem. The Textual UI is tested headlessly via `App.run_test()`, making it CI-friendly. GitHub API mode is tested against a mocked session to avoid network calls and rate limits.

---

### Architecture

* `giteyes/git_data.py` Pure functions turning a `git.Repo` into plain data structures. Completely decoupled from the UI for easy testing.
* `giteyes/sources/` Contains the `DataSource` interface and its two implementations: `LocalGitSource` and `GitHubApiSource`. The UI only interacts with the interface, making the sources perfectly interchangeable.
* `giteyes/widgets/` Small Textual widgets, each responsible for rendering one specific piece of data (e.g., the heatmap or the commit table).
* `giteyes/app.py` The main Textual `App` that composes the widgets and wires them to the provided `DataSource`.
* `giteyes/cli.py` The Typer entrypoint. It decides whether to use Local or API mode based on the target string, then launches the app.

### Project Structure

*Should look something like this:*

```text
giteyes
├── .github
│   ├──  ISSUE_TEMPLATE
│   │    ├──  bug_report.md
│   │    ├──  config.yml
│   │    ├──  feature_request.md
│   ├──  PULL_REQUEST_TEMPLATE.md
│   ├──  SECURITY.md
├── giteyes
│   ├── sources
│   │   ├── __init__.py
│   │   ├── github_api.py
│   │   └── local.py
│   └── widgets
│   │   ├── __init__.py
│   │   ├── commits.py
│   │   ├── contributors.py
│   │   ├── heatmap.py
│   │   └── hotspots.py
│   ├── __init__.py
│   ├── app.py
│   ├── app.tcss
│   ├── cli.py
│   ├── git_data.py
│   ├── models.py
├── images
│   ├── Screenshot-API.png
│   └── Screenshot-Local.png
├── tests
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_cli.py
│   ├── test_git_data.py
│   ├── test_github_api.py
│   ├── test_heatmap_hover.py
│   └── test_widget_resize.py
├── .gitignore
├── CODE_OF_CONDUCT.md
├── DEVELOPMENT.md 
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── README.md
└── uv.lock

```
