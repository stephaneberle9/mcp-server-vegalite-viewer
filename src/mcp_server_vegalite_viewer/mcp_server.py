import json
import httpx
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp import FastMCP, Context
import fastmcp
from typing import List, Any
from . import LOCALHOST
from .web_browser import web_browser
from .web_server import WebServerController, DuplicateInstanceOnSamePortError, PortInUseByAnotherServiceError

UPLOAD_DATA_TOOL_DESCRIPTION = """
A tool which allows you to upload a dataset and register it with a name for later use in visualizations.
When to use this tool:
- Use this tool when you have datasets that you want to visualize later.
How to use this tool:
- Provide the name of the dataset (for later reference) and the dataset itself.
""".strip()

VISUALIZE_DATA_TOOL_DESCRIPTION = """
A tool which allows you to produce a visualization of an already uploaded dataset based on a provided Vega-Lite specification. You can 
view the result in your web browser which opens up automatically when you use this tool for the first time.
When to use this tool:
- At times, it will be advantageous to provide the user with a visual representation of some dataset, rather than just a textual representation.
- This tool is particularly useful when the dataset is complex or has many dimensions, making it difficult to understand in a tabular format. It is not useful for singular data points.
How to use this tool:
- Prior to visualization, dataset must be uploaded and registred with a name using the upload dataset tool.
- Provide a the name of the dataset and a Vega-Lite specification describing in which way the dataset should be represented. The Vega-Lite specification must be a valid instance of the high-level Vega-Lite JSON schema that is available at https://vega.github.io/schema/vega-lite/v6.json.
""".strip()

# Create viewer manager instance internal to the MCP server
_web_server_controller = WebServerController()

logger = logging.getLogger(__name__)

class VegaLiteViewerError(Exception):
    """Raised when another service on the this machine is already using the specified port."""
    pass

@asynccontextmanager
async def mcp_lifespan(server: FastMCP) -> AsyncIterator:
    """Manage viewer web server lifecycle alongside MCP server lifecycle."""
    try:
        _web_server_controller.start(fastmcp.settings.port)
    except DuplicateInstanceOnSamePortError as e:
        logger.warning(f"Skipping start of viewer web server on port {fastmcp.settings.port}: {e}")
        logger.info(
            "This error occurs systematically when using this MCP server with Claude Desktop. Claude Desktop appears to be always launching two identical instances of every MCP "
            "server (see log files in Claude Desktop's 'logs' folder for details). This behavior is most likely a bug in Claude Desktop itself. Working around this issue by leaving "
            "the duplicate MCP server instance running (not doing so and trying to stop it would cause Claude Desktop to consider this MCP server as failed), then simply not starting "
            "a second viewer web server instance, and letting both MCP server instances share the same viewer web server instance, i.e., the one created by the first MCP server instance."
        )
    except PortInUseByAnotherServiceError as e:
        raise VegaLiteViewerError(f"Failed to start of viewer web server on port {fastmcp.settings.port}: {e}")

    try:
        yield
    finally:
        await _web_server_controller.shutdown()

# Initialize the server
mcp = FastMCP("Vega-Lite", lifespan=mcp_lifespan)

@mcp.prompt(name="Create a simple chart for a JSON dataset", description="Advises your LLM create a simple chart with a desired type (e.g., 'bar', 'line', 'pie', etc.) for a provided JSON dataset")
def create_simple_chart_for_sample_dataset(
    dataset: dict,
    chart_type: str = "bar"
) -> str:
    return f"Create a simple {chart_type} chart for the following JSON dataset and display it in my web browser: {dataset}"

# Register the upload data tool
@mcp.tool(name="upload_data", description=UPLOAD_DATA_TOOL_DESCRIPTION)
async def upload_data(name: str, data: List[Any], ctx: Context) -> str:
    """Upload and register a dataset for later use in visualizations.

    Args:
        name: Name to register the dataset under for later reference
        data: The dataset as a list of records/objects

    Returns:
        Success message confirming dataset registration

    Raises:
        ValueError: If name is empty or data is invalid
        TypeError: If data is not a list

    Note:
        FastMCP automatically converts exceptions into MCP error responses.
    """
    logger.debug("Call to 'upload_data' tool")

    # Enhanced input validation for MCPB compatibility
    if not name or not isinstance(name, str):
        raise ValueError("Dataset name must be a non-empty string")

    if not isinstance(data, list):
        raise TypeError("Data must be a list of records/objects")

    if len(data) == 0:
        raise ValueError("Dataset cannot be empty")

    # Validate that each item in data is a dictionary (record/object)
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise TypeError(f"Data item at index {i} must be a dictionary/object, got {type(item).__name__}")

    logger.info(f"Uploading dataset '{name}' (length: {len(data)})...")

    # Initialize session data storage if it doesn't exist
    if not hasattr(ctx.session, "registered_data"):
        ctx.session.registered_data = {}

    # Store the dataset in the session context
    ctx.session.registered_data[name] = data

    logger.info(f"Dataset '{name}' successfully registered with {len(data)} records")
    return f"Your dataset has been successfully uploaded and registered as '{name}' with {len(data)} records"

# Register the visualize data tool
@mcp.tool(name="visualize_data", description=VISUALIZE_DATA_TOOL_DESCRIPTION)
async def visualize_data(name: str, spec: Any, ctx: Context) -> str:
    """Create and display a visualization of a registered dataset using a Vega-Lite specification.

    Args:
        name: Name of the previously uploaded dataset to visualize
        spec: Vega-Lite specification (as dict or JSON string) describing the visualization

    Returns:
        Success message with viewer app URL

    Raises:
        ValueError: If name is empty or spec is invalid
        TypeError: If spec is not dict or string
        KeyError: If dataset name not found
        json.JSONDecodeError: If spec string is invalid JSON
        httpx.RequestError: If HTTP request to viewer web server fails
        httpx.HTTPStatusError: If viewer web server returns an error status

    Note:
        FastMCP automatically converts exceptions into MCP error responses.
    """
    logger.debug("Call to 'visualize_data' tool")

    # Enhanced input validation for MCPB compatibility
    if not name or not isinstance(name, str):
        raise ValueError("Dataset name must be a non-empty string")

    if not spec:
        raise ValueError("Vega-Lite specification cannot be empty")

    if not isinstance(spec, (dict, str)):
        raise TypeError("Vega-Lite specification must be a dictionary or JSON string")

    logger.info(f"Visualizing dataset '{name}'...")

    # (Re-)open web browser with viewer app
    web_browser.open(fastmcp.settings.port)

    # Check if session has registered data and if specified dataset exists
    if not hasattr(ctx.session, "registered_data"):
        raise KeyError("No datasets have been uploaded in this session")

    if name not in ctx.session.registered_data:
        available_datasets = list(ctx.session.registered_data.keys())
        raise KeyError(f"Dataset '{name}' not found. Available datasets: {available_datasets}")

    # Parse the provided Vega-Lite specification with enhanced error handling
    try:
        if isinstance(spec, str):
            vegalite_specification = json.loads(spec)
        else:
            vegalite_specification = spec.copy()  # Create a copy to avoid modifying original
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in Vega-Lite specification: {e.msg}", e.doc, e.pos)

    # Validate that spec is a dictionary after parsing
    if not isinstance(vegalite_specification, dict):
        raise TypeError("Vega-Lite specification must be a JSON object/dictionary")

    # Add specified dataset from session context
    data = ctx.session.registered_data[name]
    vegalite_specification["data"] = {"values": data}

    logger.info(f"Creating visualization for dataset '{name}' with {len(data)} records")

    # Send the completed visualization specification to viewer web server via HTTP POST
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{LOCALHOST}:{fastmcp.settings.port}/live-data",
                json={"spec": vegalite_specification}
            )
            response.raise_for_status()
        return f"The visualization of the '{name}' dataset has been successfully created and sent to the viewer app running in your web browser (see http://{LOCALHOST}:{fastmcp.settings.port})."
    except httpx.RequestError as e:
        raise httpx.RequestError(f"Failed to send the visualization for the '{name}' dataset to viewer web server: {e}")
    except httpx.HTTPStatusError as e:
        raise httpx.HTTPStatusError(f"The viewer web server returned status {e.response.status_code} when processing the visualization for the '{name}' dataset: {e.response.text}")
