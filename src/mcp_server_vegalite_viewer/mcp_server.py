import json
import logging
from importlib.resources import files
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.server.apps import AppConfig

UPLOAD_DATA_TOOL_DESCRIPTION = """
A tool to upload and register a JSON dataset by name for use in subsequent visualizations.
When to use this tool:
- When the user asks to visualize data, call this tool first to register the dataset, then call visualize_data.
How to use this tool:
- Provide a short, descriptive name and the dataset as a list of JSON objects (records).
- Each object should share a consistent set of keys (fields).
""".strip()

VISUALIZE_DATA_TOOL_DESCRIPTION = """
A tool to render a Vega-Lite visualization of a registered dataset directly in the chat.
When to use this tool:
- When the dataset is complex or multi-dimensional and a visual representation would be more informative than text.
- Not useful for single data points.
How to use this tool:
1. Upload the dataset first using the upload_data tool, then reference it by name here.
2. Analyze the dataset's structure and fields to determine which fields map to which visual channels (x, y, color, size, etc.).
3. Construct a Vega-Lite specification for the desired chart type. Consult the Vega-Lite documentation (https://vega.github.io/vega-lite/docs) and example gallery (https://vega.github.io/vega-lite/examples) for guidance.
4. Ensure the spec is a valid instance of the Vega-Lite schema: https://vega.github.io/schema/vega-lite/v6.json. Do not include a "data" key — it is injected automatically from the registered dataset.
""".strip()

APP_RESOURCE_URI = "ui://vegalite-viewer/view.html"

logger = logging.getLogger(__name__)

# Initialize the server
mcp = FastMCP("Vega-Lite")


@mcp.resource(APP_RESOURCE_URI, app=AppConfig())
def vegalite_viewer_app() -> str:
    """Vega-Lite visualization viewer app."""
    return (
        files("mcp_server_vegalite_viewer.resources")
        .joinpath("viewer_app.html")
        .read_text(encoding="utf-8")
    )


@mcp.prompt(
    name="Create a simple chart for a JSON dataset",
    description="Advises your LLM create a simple chart with a desired type (e.g., 'bar', 'line', 'pie', etc.) for a provided JSON dataset",
)
def create_simple_chart_for_sample_dataset(
    dataset: dict, chart_type: str = "bar"
) -> str:
    return (
        f"Create a simple {chart_type} chart for the following JSON dataset: {dataset}"
    )


# Register the upload data tool
@mcp.tool(name="upload_data", description=UPLOAD_DATA_TOOL_DESCRIPTION)
async def upload_data(name: str, data: list[Any], ctx: Context) -> str:
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
            raise TypeError(
                f"Data item at index {i} must be a dictionary/object, got {type(item).__name__}"
            )

    logger.info(f"Uploading dataset '{name}' (length: {len(data)})...")

    # Store the dataset in the session context
    registered_data: dict = await ctx.get_state("registered_data") or {}
    registered_data[name] = data
    await ctx.set_state("registered_data", registered_data)

    logger.info(f"Dataset '{name}' successfully registered with {len(data)} records")
    return f"Your dataset has been successfully uploaded and registered as '{name}' with {len(data)} records"


# Register the visualize data tool
@mcp.tool(
    name="visualize_data",
    description=VISUALIZE_DATA_TOOL_DESCRIPTION,
    app=AppConfig(resource_uri=APP_RESOURCE_URI),
)
async def visualize_data(name: str, spec: Any, ctx: Context) -> str:
    """Create and display a visualization of a registered dataset using a Vega-Lite specification.

    Args:
        name: Name of the previously uploaded dataset to visualize
        spec: Vega-Lite specification (as dict or JSON string) describing the visualization

    Returns:
        Vega-Lite specification JSON string (rendered inline in the chat by the MCP app)

    Raises:
        ValueError: If name is empty or spec is invalid
        TypeError: If spec is not dict or string
        KeyError: If dataset name not found
        json.JSONDecodeError: If spec string is invalid JSON

    Note:
        FastMCP automatically converts exceptions into MCP error responses.
    """
    logger.debug("Call to 'visualize_data' tool")

    # Enhanced input validation for MCPB compatibility
    if not name or not isinstance(name, str):
        raise ValueError("Dataset name must be a non-empty string")

    if not spec:
        raise ValueError("Vega-Lite specification cannot be empty")

    if not isinstance(spec, dict | str):
        raise TypeError("Vega-Lite specification must be a dictionary or JSON string")

    logger.info(f"Visualizing dataset '{name}'...")

    # Check if session has registered data and if specified dataset exists
    registered_data: dict | None = await ctx.get_state("registered_data")
    if not registered_data:
        raise KeyError("No datasets have been uploaded in this session")

    if name not in registered_data:
        available_datasets = list(registered_data.keys())
        raise KeyError(
            f"Dataset '{name}' not found. Available datasets: {available_datasets}"
        )

    # Parse the provided Vega-Lite specification with enhanced error handling
    try:
        if isinstance(spec, str):
            vegalite_specification = json.loads(spec)
        else:
            vegalite_specification = (
                spec.copy()
            )  # Create a copy to avoid modifying original
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in Vega-Lite specification: {e.msg}", e.doc, e.pos
        )

    # Validate that spec is a dictionary after parsing
    if not isinstance(vegalite_specification, dict):
        raise TypeError("Vega-Lite specification must be a JSON object/dictionary")

    # Inject the dataset into the spec
    data = registered_data[name]
    vegalite_specification["data"] = {"values": data}

    logger.info(
        f"Returning visualization spec for dataset '{name}' with {len(data)} records"
    )

    # Return the completed spec as JSON — the MCP app renders it inline in the chat
    return json.dumps(vegalite_specification)
