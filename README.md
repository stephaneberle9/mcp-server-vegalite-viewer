<!-- omit from toc -->
Vega-Lite Viewer MCP Server
===========================

A [Model Context Protocol](https://modelcontextprotocol.com) (MCP) server that enables creating interactive data visualizations using the [Vega-Lite](https://vega.github.io/vega-lite) grammar. Visualizations are rendered directly inside the chat using [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps) — no browser window required.

- [Usage](#usage)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [CLI Reference](#cli-reference)
  - [MCP Tools and Prompt](#mcp-tools-and-prompt)
    - [Tools](#tools)
    - [Prompt](#prompt)
  - [Example Prompts](#example-prompts)
  - [Using with MCP Inspector](#using-with-mcp-inspector)
  - [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

Usage
-----

### Prerequisites

This server requires `uv`. Install it via:

```bash
# Windows
winget install --id=astral-sh.uv -e

# macOS
brew install uv

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **macOS note:** The `curl` installer places `uv` in `~/.local/bin/` and updates your shell profile, but macOS GUI apps like Claude Desktop do not load shell startup files. Install via Homebrew to make `uv` visible to GUI apps.

See the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for more options.

### Quick Start

Add the following entry to your Claude Desktop configuration file (accessible via `Settings... > Developer > Edit Config`):

```jsonc
{
  "mcpServers": {
    "vegalite-viewer": {
      "command": "uv",
      "args": [
        "run",
        "--with-editable",
        "/path/to/mcp-server-vegalite-viewer",
        "mcp-server-vegalite-viewer"
      ]
    }
  }
}
```

Restart Claude Desktop to apply changes. The server is ready when `vegalite-viewer` appears in the list of connected MCP servers.

> ℹ️ **Note:** Rendering visualizations inline in the chat requires a client that supports [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps), such as Claude Desktop or Claude.ai.

### CLI Reference

| Flag       | Description                                                                    |
|------------|--------------------------------------------------------------------------------|
| `--silent` | Show only error messages                                                       |
| `--debug`  | Enable detailed debug logging (also settable via `VEGALITE_VIEWER_DEBUG=1`)    |

### MCP Tools and Prompt

#### Tools

| Tool             | Description                                                                    |
|------------------|--------------------------------------------------------------------------------|
| `upload_data`    | Upload a JSON dataset and register it by name for later use in visualizations  |
| `visualize_data` | Render a registered dataset as a Vega-Lite chart, displayed inline in the chat |

**Workflow:** call `upload_data` first to register the dataset, then call `visualize_data` with a [Vega-Lite specification](https://vega.github.io/schema/vega-lite/v6.json) to produce the chart. The same dataset can be visualized multiple times with different specs.

#### Prompt

| Prompt                                    | Description                                                                             |
|-------------------------------------------|-----------------------------------------------------------------------------------------|
| `Create a simple chart for a JSON dataset`| Instructs the LLM to create a chart of a chosen type (`bar`, `line`, `pie`, etc.) for a provided JSON dataset |

### Example Prompts

```text
Create a simple bar chart for the following JSON dataset:
[
  {"category": "Alpha",   "value": 4},
  {"category": "Bravo",   "value": 6},
  {"category": "Charlie", "value": 10},
  {"category": "Delta",   "value": 3},
  {"category": "Echo",    "value": 7},
  {"category": "Foxtrot", "value": 9}
]
```

### Using with MCP Inspector

Create an `mcp.json` file:

```jsonc
{
  "mcpServers": {
    "vegalite-viewer": {
      "command": "uv",
      "args": [
        "run",
        "mcp-server-vegalite-viewer",
        "--debug"
      ]
    }
  }
}
```

Start the inspector from a terminal:

```bash
npx -y @modelcontextprotocol/inspector --config mcp.json --server vegalite-viewer
```

In your browser:

- Click `Connect` to start the server
- Go to `Tools > List Tools` to see the available tools
- Find server logs under `Server Notifications` and in `%TEMP%\mcp_server_vegalite_viewer.log` (Windows) or `${TMPDIR:-/tmp}/mcp_server_vegalite_viewer.log` (Linux/macOS)

### Troubleshooting

**Visualization not rendering inline**

The client must support [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps). In clients without MCP Apps support the tool still works — the Vega-Lite JSON spec is returned as text, which the LLM can describe or the user can paste into [Vega Editor](https://vega.github.io/editor).

**Server fails to start in Claude Desktop**

Check the Claude Desktop logs:

- **Windows:** `%LOCALAPPDATA%\Claude\Logs\mcp-server-vegalite-viewer.log`
- **macOS:** `~/Library/Logs/Claude/mcp-server-vegalite-viewer.log`

Or go to `Settings > Developer`, select `vegalite-viewer` and click `Open Logs Folder`.

**Still having issues?**

Run the server with `--debug` and open an issue on GitHub with the relevant log output.

Contributing
------------

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, building the React app, code quality checks, and the release process.
