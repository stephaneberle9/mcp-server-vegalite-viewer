**Vega-Lite Viewer MCP Server**

A [Model Context Protocol](https://modelcontextprotocol.com) (MCP) server that enables creating and displaying interactive data visualizations using the [Vega-Lite](https://vega.github.io/vega-lite) grammar. This server provides tools to generate charts from data and automatically opens them in a web browser for immediate viewing.

- [Development](#development)
  - [Setup](#setup)
  - [Run](#run)
    - [Inside dev environment](#inside-dev-environment)
    - [Outside dev environment](#outside-dev-environment)
    - [With MCP Inspector](#with-mcp-inspector)
  - [Check](#check)
    - [Enable automatic execution on git commit](#enable-automatic-execution-on-git-commit)
    - [Manual execution](#manual-execution)
  - [Package](#package)
    - [MCP Bundle (formerly Desktop Extension)](#mcp-bundle-formerly-desktop-extension)
    - [Python Package Distribution (rarely needed)](#python-package-distribution-rarely-needed)
- [Usage](#usage)
  - [Connect MCP client](#connect-mcp-client)
    - [Claude Desktop](#claude-desktop)
      - [Option 1: One-click installation using MCP Bundle (recommended)](#option-1-one-click-installation-using-mcp-bundle-recommended)
      - [Option 2: Manual configuration using the sources](#option-2-manual-configuration-using-the-sources)
  - [Example prompts](#example-prompts)

# Development

## Setup

- Install [Python 3.12](https://www.python.org/downloads) or later
- Install required development tools:

  ```bash
  # Install build tools and uv package manager
  python -m pip install build uv
  ```

## Run

### Inside dev environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source ./.venv/bin/activate  # Linux/macOS

# Install project in editable mode with live code reloading
uv pip install -e .

# Run the MCP server (choose one option):

# Option 1: Run as Python module
mcp-server-vegalite-viewer [options]
# or
python -m mcp_server_vegalite_viewer [options]

# Option 2: Run with FastMCP CLI using MCP configuration file
fastmcp run mcp.json

# Stop the server
# Press Ctrl+C to exit

# Deactivate virtual environment when done
deactivate
```

### Outside dev environment

To treat this project like an installed package for a one-off run:

```bash
# Change to any non-project directory
cd /path/to/some/other/directory

# Run the server directly from project path
uv run "/absolute path/to/mcp-server-vegalite-viewer project" mcp-server-vegalite-viewer [options]

# For development mode with live code reloading (editable install)
uv run --with-editable "/absolute path/to/mcp-server-vegalite-viewer project" mcp-server-vegalite-viewer [options]
```

### With MCP Inspector

```bash
# Start and open MCP inspector in your browser
npx @modelcontextprotocol/inspector
```

- MCP Server configuration:

  | Setting            | Value                                                                                                                                                                                          |
  | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | **Transport Type** | `STDIO`                                                                                                                                                                                        |
  | **Command**        | **Windows:**<br>`\absolute path\to\mcp-server-vegalite-viewer project\.venv\Scripts\python.exe`<br>**Linux/macOS:**<br>`/absolute path/to/mcp-server-vegalite-viewer project/.venv/bin/python` |
  | **Arguments**      | `-m mcp_server_vegalite_viewer --debug`                                                                                                                                                        |

- Connect to MCP server: `Connect` or `Restart`

  > :information*source: The local \_Vega-Lite Viewer* MCP server instance is started automatically

- Find MCP server logs in `%TEMP%\mcp-server-vegalite-viewer.log` (Windows) or `${TMPDIR:-/tmp}/mcp-server-vegalite-viewer.log` (Linux/macOS)

## Check

This project uses `pre-commit` hooks for running static checks to maintain high code quality standards. These static checks include:

- **Ruff**: Python linting and code formatting
- **ty**: Modern type checking for Python
- **Prettier**: JSON, YAML, and Markdown formatting
- **Codespell**: Common spelling error detection
- **pyproject.toml validation**: Project configuration validation

### Enable automatic execution on git commit

```bash
# Install pre-commit hooks
uv run pre-commit install
```

### Manual execution

```bash
# Run all checks on all files
uv run pre-commit run --all-files

# Run individual tools
uv run ruff format          # Code formatting
uv run ruff check --fix     # Linting with auto-fix
uv run ty check             # Type checking
```

## Package

### MCP Bundle (formerly Desktop Extension)

To create a MCP Bundle (MCPB) for one-click installation in _Claude Desktop_:

```bash
# Install MCPB CLI globally
npm install -g @anthropic-ai/mcpb

# Validate MCPB manifest (optional)
mcpb validate manifest.json  # Windows
mcpb validate manifest.json  # Linux/macOS

# Install "fat" package including this MCP server package and all dependencies into `lib` subfolder
uv pip install . --target lib --upgrade

# Create MCP Bundle
mcpb pack . dist\vegalite-viewer.mcpb  # Windows
mcpb pack . dist/vegalite-viewer.mcpb  # Linux/macOS
```

This will create a `dist` folder containing a `vegalite-viewer.mcpb` file that can be easily installed in _Claude Desktop_ as an extension (see [here](https://www.anthropic.com/engineering/desktop-extensions) for details).

### Python Package Distribution (rarely needed)

For publishing to PyPI or integrating with Python package managers:

```bash
# Create and activate virtual environment
uv venv
.venv\Scripts\activate  # Windows
source ./.venv/bin/activate  # Linux/macOS

# Install project dependencies
uv pip install .

# Build distribution packages
uv build
```

This will create a `dist` folder containing an `mcp_server_vegalite-viewer X.X.X.tar.gz` and an `mcp_server_vegalite-viewer X.X.X-py3-none-any.whl`.

# Usage

## Connect MCP client

### Claude Desktop

#### Option 1: One-click installation using MCP Bundle (recommended)

1. Create the MCPB bundle (see previous section)
2. In _Claude Desktop_, go to `Settings...` > `Extensions`
3. Drag & drop the `vegalite-viewer.mcpb` file from the `dist` folder into the `Extensions` list
4. Click `Install`, wait (patiently) until installation is complete, and close the install dialog
5. Locate the `vegalite-viewer` in the `Extensions` list, click `Configure` and adjust viewer web server port and debug logging to your liking

> :no*entry: Apparently, MCP Bundles don't support Python packages yet. While the installation as describe above succeeds, the subsequent start of the \_Vega-Lite Viewer* MCP server fails. Opt for manual installation as a workaround for the time being (see below)

#### Option 2: Manual configuration using the sources

- Open _Claude Desktop_ configuration JSON file (accessible from _Claude Desktop_ > `Settings...` > `Developer` > `Edit config`)
- Add the following entry under `mcpServers`:

  ```json
  {
    "mcpServers": {
      "vegalite-viewer": {
        "command": "uv",
        "args": [
          "run",
          "--with-editable",
          "/absolute path/to/mcp-server-vegalite-viewer project",
          "mcp-server-vegalite-viewer",
          "--port",
          "8080",
          "--lazy-view"
        ]
      }
    }
  }
  ```

## Example prompts

The following example prompts can be used to test the _Vega-Lite Viewer_ MCP server functionality in _Claude Desktop_ or any other MCP client.

- Create a simple bar chart for the following JSON dataset and display it in my web browser:
  [
  {
  "category": "Alpha",
  "value": 4
  },
  {
  "category": "Bravo",
  "value": 6
  },
  {
  "category": "Charlie",
  "value": 10
  },
  {
  "category": "Delta",
  "value": 3
  },
  {
  "category": "Echo",
  "value": 7
  },
  {
  "category": "Foxtrot",
  "value": 9
  }
  ]
