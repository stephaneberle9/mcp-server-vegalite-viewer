# Claude Code Configuration

This file contains information for Claude Code about how to work with this project.

## Project Overview

A data visualization MCP (Model Context Protocol) server using Vega-Lite and FastMCP. Visualizations are rendered directly in the chat using MCP Apps — no browser window required.

## Development Setup

### Initial Setup

```bash
python -m pip install build uv
uv venv
.venv\Scripts\activate
uv pip install -e .
```

### Running the Server

```bash
mcp-server-vegalite-viewer
```

or

```bash
python -m mcp_server_vegalite_viewer
```

### Testing Outside Project Environment

```bash
uvx --from "W:\GitLab\mcp-server-vegalite-viewer" mcp-server-vegalite-viewer
```

Add `--reinstall` flag when testing changes:

```bash
uvx --from "W:\GitLab\mcp-server-vegalite-viewer" --reinstall mcp-server-vegalite-viewer
```

## Build Commands

### React App (run after changing files in `app/`)

```bash
cd app && npm install && npm run build
```

The build output is committed to `src/mcp_server_vegalite_viewer/resources/viewer_app.html`.

### Python Package Building

```bash
uv build
```

### Type Checking

```bash
pyright
```

## Key Files

- `src/mcp_server_vegalite_viewer/mcp_server.py` - MCP server: tools, MCP App resource
- `src/mcp_server_vegalite_viewer/__main__.py` - CLI entry point
- `src/mcp_server_vegalite_viewer/resources/viewer_app.html` - Built MCP App (React + Vega-Embed, do not edit manually)
- `app/` - React + Vite source for the MCP App
- `app/src/App.tsx` - React component that renders Vega-Lite specs

## Dependencies

- Python 3.12+
- fastmcp >= 3.0.0

## Testing

```bash
pytest -v
```
