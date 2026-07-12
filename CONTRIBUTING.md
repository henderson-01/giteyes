# Contributing to giteyes

First off, thank you for considering contributing to **giteyes**!

Whether you're fixing a bug, adding a new Textual widget, or improving the GitHub API integration, your help is appreciated. This document outlines the process for getting your local environment set up and how to submit your changes.

## 🛑 Before You Begin: Discuss Major Changes

To save your valuable time, **if you plan to add a major feature or make significant architectural changes, please open an Issue to discuss it first.** This ensures your proposed changes align with the project's roadmap and prevents you from spending hours on a Pull Request that might not be merged. (For minor bug fixes or small UI tweaks, feel free to just open a PR!)

---

## Local Development Setup

We use [uv](https://docs.astral.sh/uv/) to manage dependencies and virtual environments. It keeps the development process fast and isolated.

* 1: Clone the repository

```bash
git clone https://github.com/henderson-01/giteyes.git
cd giteyes

```

* 2: Sync the environment**

```bash
uv sync

```

This command automatically creates a `.venv`, locks dependencies, and installs `giteyes` in editable mode.

* 3: Run the application
You can run the dashboard using `uv run` to ensure it executes within the isolated environment:

```bash
# Test against the giteyes repo itself
uv run giteyes 

# Test against a remote repo
uv run giteyes https://github.com/henderson-01/random-quotes

```

*(Note: If you are testing the GitHub API mode extensively, it is highly recommended to export a `GITHUB_TOKEN` to avoid rate limits during development.)*

---

## Understanding the Architecture

Before writing code, it helps to know where things live. `giteyes` separates the data layer from the UI to make testing and adding features straightforward.

| Directory / File | Purpose |
| --- | --- |
| `giteyes/cli.py` | Typer entrypoint. Parses CLI arguments and determines if the target is local or an API call. |
| `giteyes/app.py` | The main Textual UI application that wires the data sources to the widgets. |
| `giteyes/sources/` | Contains the `DataSource` interface. All new data gathering must implement this interface via `LocalGitSource` or `GitHubApiSource`. |
| `giteyes/git_data.py` | Pure data processing functions. Decoupled from the UI to ensure easy testing. |
| `giteyes/widgets/` | Individual Textual components (e.g., heatmap, commit tables). Keep these focused on rendering a single piece of data. |

---

## Code Style & Linting

We aim to keep the codebase clean and consistent. Please ensure your code follows standard Python formatting guidelines.

If you are adding new files or functions, match the existing style of the repository. (If we introduce strict linters like `ruff` or `black` in the future, please ensure you run them via `uv run` before committing).

---

## Testing (Strict Policy)

Testing is a first-class citizen in `giteyes`. We have a strict policy to ensure that new contributions **do not break the application**. Because we deal with file systems, git histories, and terminal UIs, we use specific patterns to keep tests fast and reliable.

First, ensure you have the development dependencies installed:

```bash
uv sync --extra dev

```

Then, run the tests:

```bash
uv run pytest

```

**All tests MUST pass** before you submit a merge request.

**Testing Guidelines:**

* **No global system changes:** Tests that require a git repository use scripted, throwaway git repos with dated commits (check `tests/conftest.py`). Do not write tests that depend on the developer's global git config or local filesystem state.
* **Headless UI Testing:** Textual UI components are tested headlessly using `App.run_test()`. This ensures the UI renders correctly in CI environments without needing an actual terminal.
* **Mock the Network:** Any tests targeting `GitHubApiSource` must use the mocked session. Do not write tests that make live calls to the GitHub REST API, as this will cause CI failures due to rate limiting.

---

## Submitting a Pull Request

To maintain the quality and stability of `giteyes`, all Pull Requests must adhere to the following requirements:

1. **Fork and branch:** Fork the repository and create a new branch from `main` (e.g., `feature/add-new-widget` or `fix/api-rate-limit-bug`).
2. **Keep it focused:** Try to keep your PR scoped to a single feature or bug fix.
3. **Write tests:** If you are adding a new feature or fixing a bug, please include tests that cover the new behavior.
4. **Run the suite (Mandatory):** Ensure all tests pass locally by running `uv run pytest`. PRs with failing tests will not be reviewed or merged.
5. **Verify the application:** You must manually verify that `uv` is still managing the project correctly and that the application launches without errors by running `uv run giteyes` against a test repository.
6. **Provide clear PR details & Screenshots:** Your PR description must explicitly state what you changed and why. **If your contribution affects the UI in any way or adds a visual feature, you MUST include a screenshot** of the terminal in your PR description demonstrating the changes.

---

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms. *(Note: A Code of Conduct file will be available in the repository root.)*

## License

By contributing to **giteyes**, you agree that your contributions will be licensed under its MIT License.
