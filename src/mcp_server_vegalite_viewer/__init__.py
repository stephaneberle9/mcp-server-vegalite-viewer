"""Vega-Lite Viewer MCP server."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("mcp_server_vegalite_viewer")
except PackageNotFoundError:
    # If the package is not installed, use a development version
    __version__ = "0.0.0-dev"

# Global constants
LOCALHOST = "localhost"
