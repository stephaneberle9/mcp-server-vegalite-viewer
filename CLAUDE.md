# Claude Code Configuration

This file contains information for Claude Code about how to work with this project.

## Project Overview
A data visualization MCP (Model Context Protocol) server using Vega-Lite and FastAPI. This server allows creating and displaying data visualizations in a web browser through MCP tools.

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

### Package Building
```bash
uv build
```

### MCPB Bundle Creation
```bash
python build_mcpb_bundle.py
```

### Type Checking
```bash
pyright
```

## Key Files
- `src/mcp_server_vegalite_viewer/mcp_server.py` - Main MCP server implementation with enhanced validation
- `src/mcp_server_vegalite_viewer/__main__.py` - Enhanced CLI entry point with debug support
- `src/mcp_server_vegalite_viewer/web_server.py` - FastAPI web server
- `src/mcp_server_vegalite_viewer/viewer_manager.py` - Visualization management
- `src/mcp_server_vegalite_viewer/web_browser.py` - Browser integration
- `src/mcp_server_vegalite_viewer/resources/` - Static resources (HTML templates, JSON specs)
- `mcpb-bundle/manifest.json` - MCPB configuration and user settings
- `mcpb-bundle/server/main.py` - MCPB entry point
- `build_mcpb_bundle.py` - MCPB bundle creation script

## Dependencies
- Python 3.12+
- fastmcp >= 2.11.0 (for session context support)
- FastAPI
- Uvicorn
- httpx
- psutil

## Testing
Run unit tests for enhanced validation:
```bash
pytest mcpb-bundle/server/tests/ -v
```