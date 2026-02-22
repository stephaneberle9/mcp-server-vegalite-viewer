<!-- omit from toc -->
Contributing
============

- [Development Setup](#development-setup)
  - [Prerequisites](#prerequisites)
  - [Initial Setup](#initial-setup)
- [Building the React App](#building-the-react-app)
- [Running the Server](#running-the-server)
  - [Inside dev environment](#inside-dev-environment)
  - [With MCP Inspector](#with-mcp-inspector)
- [Code Quality](#code-quality)
  - [Enable automatic execution on git commit](#enable-automatic-execution-on-git-commit)
  - [Manual execution](#manual-execution)
- [Building the Python Package](#building-the-python-package)
- [Release Process](#release-process)

Development Setup
-----------------

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — Python package and project manager
- Node.js 18+ with npm — required only for rebuilding the React app (see [Building the React App](#building-the-react-app))

### Initial Setup

Install required development tools:

```bash
# Install build tools and uv package manager
python -m pip install build uv
```

Clone the repository and install the package in editable mode:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source ./.venv/bin/activate  # Linux/macOS

# Install project in editable mode with live code reloading
uv sync
```

Building the React App
----------------------

The MCP App that renders visualizations is a React + Vite app in [`app/`](app/). Its
build output — a self-contained single HTML file — is committed to
[`src/mcp_server_vegalite_viewer/resources/viewer_app.html`](src/mcp_server_vegalite_viewer/resources/viewer_app.html)
so end users need no Node.js to run the server.

Rebuild whenever you change files inside `app/`:

```bash
cd app && npm install && npm run build
```

Commit `src/mcp_server_vegalite_viewer/resources/viewer_app.html` along with any `app/`
changes.

Running the Server
----------------------------------

### Inside dev environment

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source ./.venv/bin/activate  # Linux/macOS

# Start the server
mcp-server-vegalite-viewer --debug

# Press Ctrl+C to exit

# Deactivate virtual environment when done
deactivate
```

### With MCP Inspector

To inspect the server interactively, create an `mcp.json` file (it is
git-ignored) containing:

```jsonc
{
  "mcpServers": {
    "vegalite-viewer": {
      "command": "uv",
      "args": [
        "run",
        "--with-editable",
        ".",
        "mcp-server-vegalite-viewer",
        "--debug"
      ]
    }
  }
}
```

From a terminal, start the MCP Inspector:

```bash
npx -y @modelcontextprotocol/inspector --config mcp.json --server vegalite-viewer
```

Code Quality
------------

Pre-commit hooks are configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

### Enable automatic execution on git commit

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source ./.venv/bin/activate  # Linux/macOS

# Install pre-commit hooks
uv run pre-commit install
```

### Manual execution

```bash
# Run all checks on all files
uv run pre-commit run --all-files
```

Hooks that run on every commit:

| Hook          | Purpose                        |
|---------------|--------------------------------|
| `ruff-check`  | Python linting (with auto-fix) |
| `ruff-format` | Python code formatting         |
| `ty check`    | Python type checking           |
| `prettier`    | YAML / JSON formatting         |
| `codespell`   | Spell checking                 |

Building the Python Package
----------------------------

For publishing to PyPI or integrating with Python package managers:

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source ./.venv/bin/activate  # Linux/macOS

# Install project dependencies
uv sync --no-dev

# Build distribution packages
uv build
```

This will create a `dist` folder containing an
`mcp_server_vegalite_viewer-X.X.X.tar.gz` and an
`mcp_server_vegalite_viewer-X.X.X-py3-none-any.whl` file.

Release Process
---------------

1. Ensure all changes are committed and the `main` branch is up to date.

2. Create and push a version tag:

   ```bash
   git tag v1.x.x
   git push origin v1.x.x
   ```

3. Create a GitHub release from the tag and add release notes.

The package version is derived automatically from the git tag by
[uv-dynamic-versioning](https://github.com/nicoddemus/uv-dynamic-versioning).
