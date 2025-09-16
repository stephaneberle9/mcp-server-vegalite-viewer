**Vega-Lite Viewer MCP Server**

A Model Context Protocol (MCP) server that enables creating and displaying interactive data visualizations using Vega-Lite. This server provides tools to generate charts from data and automatically opens them in a web browser for immediate viewing.

- [Development](#development)
  - [Setup](#setup)
  - [Run inside dev environment](#run-inside-dev-environment)
  - [Run outside dev environment](#run-outside-dev-environment)
  - [Test with MCP Inspector](#test-with-mcp-inspector)
  - [Packaging](#packaging)
    - [MCP Bundle (formerly Desktop Extension)](#mcp-bundle-formerly-desktop-extension)
    - [Python Package Distribution (rarely needed)](#python-package-distribution-rarely-needed)
- [Usage](#usage)
  - [Connect MCP client](#connect-mcp-client)
    - [Claude Desktop](#claude-desktop)
      - [Option 1: One-click installation using MCP Bundle (recommended)](#option-1-one-click-installation-using-mcp-bundle-recommended)
      - [Option 2: Manual configuration](#option-2-manual-configuration)
  - [Example prompts](#example-prompts)

# Development

## Setup

- Install [Python 3.12](https://www.python.org/downloads) or later
- Install required development tools:
  
  ```bash
  python -m pip install build uv
  ```

## Run inside dev environment

1. `uv venv`

2. `.venv\Scripts\activate` (Windows) or `source ./.venv/bin/activate` (macOS/Linux)

3. `uv pip install -e .`

4. Run

    - as Python module: `mcp-server-vegalite-viewer [options]` or `python -m mcp_server_vegalite_viewer [options]`
    - with FastMCP CLI using MCP configuration file as entrypoint: `fastmcp run mcp.json`

5. Press `Ctrl+C` to exit the server

6. `deactivate`

## Run outside dev environment

To treat this project like an installed package for a one-off run, you can use the following command:

1. cd into any non-project directory of your choice

2. `uvx --from "/absolute path/to/mcp-server-vegalite-viewer project" mcp-server-vegalite-viewer [options]`

> :information_source: When you makes changes to the project's sources, add the `--reinstall` option to 
> the command to ensure that these changes are taken into account upon subsequent reruns:

```bash
uvx --from "/path/to/mcp-server-vegalite-viewer project" --reinstall mcp-server-vegalite-viewer [options]
```

> :information_source: If you see the following warning you can ignore as it applies when targeting published packages
> but not to packages from a local path.

```
warning: Tools cannot be reinstalled via uvx; use uv tool upgrade --all --reinstall to 
reinstall all installed tools, or uvx package@latest to run the latest version of a tool.
```

## Test with MCP Inspector

- Start and open MCP inspector in your browser: `npx @modelcontextprotocol/inspector`

- MCP Server configuration:
  - Transport Type: `STDIO`
  - Command: 
    - Windows: `\absolute path\to\mcp-server-vegalite-viewer project\.venv\Scripts\python.exe`
    - macOS/Linux: `/absolute path/to/mcp-server-vegalite-viewer project/.venv/bin/python`
  - Arguments: `-m mcp_server_vegalite_viewer --debug`

- Connect to MCP server: `Connect` or `Restart`

  > :information_source: The local Vega-Lite Viewer MCP server instance is started automatically

- Find MCP server logs in `%TEMP%\mcp-server-vegalite-viewer.log` (Windows) or `${TMPDIR:-/tmp}/mcp-server-vegalite-viewer.log` (macOs/Linux)

## Packaging

### MCP Bundle (formerly Desktop Extension)

To create a MCP Bundle (MCPB) for one-click installation in Claude Desktop:

1. Install MCPB CLI: `npm install -g @anthropic-ai/mcpb`

2. Validate MCPB manifest (optional): `mcpb validate manifest.json`

3. Install "fat" package including this MCP server package and all dependencies into `lib` subfolder: `uv pip install . --target lib --upgrade`

4. Create MCP Bundle: `mcpb pack . dist\vegalite-viewer.mcpb` (Windows) or `mcpb pack . dist/vegalite-viewer.mcpb` (macOS/Linux)

This will create a `dist` folder containing a `vegalite-viewer.mcpb` file that can be easily installed in Claude Desktop as an extension (see [here](https://www.anthropic.com/engineering/desktop-extensions) for details).

### Python Package Distribution (rarely needed)

For publishing to PyPI or integrating with Python package managers:

1. `uv venv`

2. `.venv\Scripts\activate` (Windows) or `source ./.venv/bin/activate` (macOS/Linux)

3. `uv pip install .`

4. `uv build`

This will create a `dist` folder containing an `mcp_server_vegalite-viewer X.X.X.tar.gz` and an `mcp_server_vegalite-viewer X.X.X-py3-none-any.whl`.

# Usage

## Connect MCP client

### Claude Desktop

#### Option 1: One-click installation using MCP Bundle (recommended)

1. Create the MCPB bundle (see previous section)
2. In Claude Desktop, go to `Settings...` > `Extensions`
3. Drag & drop the `vegalite-viewer.mcpb` file from the `dist` folder into the `Extensions` list
4. Click `Install`, wait (patiently) until installation is complete, and close the install dialog
5. Locate the `vegalite-viewer` in the `Extensions` list, click `Configure` and adjust viewer web server port and debug logging to your liking

> :no_entry: Apparently, MCP Bundles don't support Python packages yet. While the installation as describe above succeeds, the subsequent start of the Vega-Lite Viewer MCP server fails. Opt for manual installation as a workaround for the time being (see below)

#### Option 2: Manual configuration

- Open Claude Desktop configuration JSON file (accessible from Claude Desktop > `Settings...` > `Developer` > `Edit config`)
- Add the following entry under `mcpServers`:

  ```json
  {
    "mcpServers": {
      "vegalite-viewer": {
        "command": "uvx",
        "args": [
          "--from",
          "/absolute path/to/mcp-server-vegalite-viewer project",
          "--reinstall",
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