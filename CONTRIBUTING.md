<!-- omit from toc -->
Contributing
============

- [Development Setup](#development-setup)
  - [Prerequisites](#prerequisites)
  - [Initial Setup](#initial-setup)
- [Building the React App](#building-the-react-app)
- [Running the Server in Development](#running-the-server-in-development)
- [Code Quality](#code-quality)
- [Building the Python Package](#building-the-python-package)
- [Release Process](#release-process)

Development Setup
-----------------

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — Python package and project manager
- Node.js 18+ with npm — required only for rebuilding the React app (see [Building the React App](#building-the-react-app))

### Initial Setup

Clone the repository and install the package in editable mode:

```bash
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

Running the Server in Development
----------------------------------

Start the server directly from the project:

```bash
mcp-server-vegalite-viewer --debug
```

To inspect the server interactively, create an `mcp.json` file (it is git-ignored) and
start [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

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

```bash
npx -y @modelcontextprotocol/inspector --config mcp.json --server vegalite-viewer
```

Code Quality
------------

Pre-commit hooks are configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).
Install them after the initial setup:

```bash
pre-commit install
```

Run all hooks manually:

```bash
pre-commit run --all-files
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

```bash
uv build
```

Output is written to `dist/`.

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
