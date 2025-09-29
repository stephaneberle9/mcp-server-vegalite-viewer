import asyncio
import copy
import importlib.resources as resources
import json
import logging
import os
import socket
import tempfile
import time
import warnings
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from uvicorn.config import LOGGING_CONFIG

from . import LOCALHOST
from .viewer_manager import ViewerManager

# Suppress specific deprecation warnings from websockets/uvicorn until they fix the compatibility issue. These warnings
# come from uvicorn's internal usage of websockets library, not our code
# (see https://github.com/encode/uvicorn/discussions/2476 for details)
warnings.filterwarnings(
    "ignore", message="websockets.legacy is deprecated", category=DeprecationWarning
)
warnings.filterwarnings(
    "ignore",
    message="websockets.server.WebSocketServerProtocol is deprecated",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message="remove second argument of ws_handler",
    category=DeprecationWarning,
)

WEB_SERVER_PORT_LOCK_SECS = 600
WEB_SERVER_CONTROLLER_STATE_FILE = os.path.join(
    os.path.expanduser("~"), ".mcp", __package__, ".web_server_controller_state.json"
)
WEB_SERVER_LOCKED_PORTS_KEY = "locked_ports"

logger = logging.getLogger(__name__)


class DuplicateInstanceOnSamePortError(Exception):
    """Raised when another viewer web server instance is already is running on the specified port."""

    def __init__(self, conflicting_port: int | None):
        self.conflicting_port = conflicting_port

    def __str__(self):
        return (
            "Another viewer web server instance is already running "
            f"on port {self.conflicting_port}"
            if self.conflicting_port
            else "and potentially using the same port"
        )


class PortInUseByAnotherServiceError(Exception):
    """Raised when another service on the this machine is already using the specified port."""

    def __init__(self, port: int):
        self.port = port

    def __str__(self):
        return f"Port {self.port} is already in use by another service on this machine"


# Create viewer manager instance internal to web server
_viewer_manager = ViewerManager()


# Request model for live data endpoint
class LiveDataRequest(BaseModel):
    spec: Any


app = FastAPI()


@app.get("/")
async def root(request: Request):
    """Renders viewer.html by substituting {{port}} placeholder(s) with actual web server port and returns resulting
    HTML content to the client (web browser)."""
    # Load viewer html template
    viewer_html_template = resources.read_text(
        f"{__package__}.resources", "viewer.html"
    )

    # Fill in the actual web server port
    viewer_html_content = viewer_html_template.replace(
        "{{port}}", str(request.url.port)
    )

    # Return response containing the rendered viewer HTML content
    return Response(content=viewer_html_content, media_type="text/html")


@app.get("/favicon.ico")
async def favicon():
    """Redirects favicon requests to Vega-Lite's official favicon."""
    return RedirectResponse(url="https://vega.github.io/favicon.ico", status_code=301)


@app.get("/sample-data")
async def sample_data():
    """Loads and broadcasts sample visualization specification to connected clients (web browsers) for demonstration purposes."""
    try:
        # Load sample visualization specification
        sample_spec_content = resources.read_text(
            f"{__package__}.resources", "sample-visualization-spec.json"
        )
        sample_spec_json = json.loads(sample_spec_content)

        # Broadcast visualization to all connected clients
        await _viewer_manager.broadcast_visualization(json.dumps(sample_spec_json))

        return {
            "status": "success",
            "message": "Sample visualization specification successfully sent to connected clients",
        }
    except Exception as e:
        msg = f"Failed to broadcast live visualization specification: {e}"
        logger.error(msg)
        raise HTTPException(status_code=500, detail=msg)


@app.post("/live-data")
async def live_data(request: LiveDataRequest):
    """Receives visualization specifications composed of a Vega-Lite specification and a dataset and broadcasts them to
    connected visualization clients (web browsers)."""
    try:
        # Convert visualization specification to JSON string if it's not already
        if isinstance(request.spec, str):
            spec_json = request.spec
        else:
            spec_json = json.dumps(request.spec)

        # Broadcast visualization specification to all connected clients
        await _viewer_manager.broadcast_visualization(spec_json)

        return {
            "status": "success",
            "message": "Visualization specification successfully sent to connected clients",
        }
    except Exception as e:
        msg = f"Failed to broadcast live visualization specification: {e}"
        logger.error(msg)
        raise HTTPException(status_code=500, detail=msg)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication with visualization clients (web browsers)."""
    await _viewer_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive, ignore input
    except Exception:
        _viewer_manager.disconnect(websocket)


class WebServerController:
    def __init__(self):
        self._port = None
        self._locked_ports = {}
        self._web_server = None
        self._web_server_task = None

    def _load_state(self):
        """Load current state from state file."""
        if os.path.exists(WEB_SERVER_CONTROLLER_STATE_FILE):
            try:
                # Load persisted state
                with open(WEB_SERVER_CONTROLLER_STATE_FILE) as f:
                    # Do nothing if state file is empty or contains only whitespace
                    content = f.read().strip()
                    if not content:
                        return

                    # Try to parse as JSON
                    state = json.loads(content)
                    persisted_ports = state.get(WEB_SERVER_LOCKED_PORTS_KEY, {})

                    # Filter out stale entries
                    now = time.time()
                    for port_str, locked_until in persisted_ports.items():
                        # Expired?
                        if now >= locked_until:
                            continue
                        # Port no longer busy?
                        if not self._is_port_in_use(int(port_str)):
                            continue
                        self._locked_ports[int(port_str)] = locked_until
            except json.JSONDecodeError as e:
                logger.warning(f"State file contains invalid JSON: {e}")
                self._locked_ports = {}
                raise
            except Exception as e:
                logger.warning(f"Failed to load web server controller state: {e}")
                self._locked_ports = {}
                raise

    def _save_state(self):
        """Save current state to state file."""
        try:
            # Make sure that parent folder of state file exists
            os.makedirs(
                os.path.dirname(WEB_SERVER_CONTROLLER_STATE_FILE), exist_ok=True
            )

            # Persist current state
            with open(WEB_SERVER_CONTROLLER_STATE_FILE, "w") as f:
                state = {
                    WEB_SERVER_LOCKED_PORTS_KEY: {
                        str(port): locked_until
                        for port, locked_until in self._locked_ports.items()
                    }
                }
                json.dump(state, f, indent=2)
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to save web server controller state: {e}")
            raise

    def _remove_state(self):
        """Remove the entire state file."""
        try:
            if os.path.exists(WEB_SERVER_CONTROLLER_STATE_FILE):
                os.remove(WEB_SERVER_CONTROLLER_STATE_FILE)
        except Exception as e:
            logger.warning(f"Failed to remove web server controller state: {e}")

    def _lock_port(self, port: int, locked_until: float):
        """Add a port to the locked ports list."""
        try:
            self._load_state()
            self._locked_ports[port] = locked_until
            self._save_state()
        except Exception:
            # State file access conflict is a strong indicator that another viewer web server instance is about to
            # manipulate it - we cannot really know which port it is targeting but to be on the safe side, let's assume
            # that it is the same port
            raise DuplicateInstanceOnSamePortError(None)

    def _unlock_port(self, port: int):
        """Remove a port from the locked ports list."""
        self._load_state()
        self._locked_ports.pop(port, None)
        if self._locked_ports:
            self._save_state()
        else:
            # No locked ports left, remove the file
            self._remove_state()

    def is_already_running_on_same_port(self, port: int) -> bool:
        """Check if another viewer web server instance is already running on the specified port."""
        self._load_state()
        return port in self._locked_ports

    def _is_port_in_use(self, port: int) -> bool:
        """Check if given port is in use by another viewer web server instance or another service on this machine."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((LOCALHOST, port))
                return False
            except OSError:
                return True

    def _get_log_config(self) -> dict[str, Any]:
        # Get the log level from the root logger
        log_level = logging.getLogger().getEffectiveLevel()

        # Get the log file from the root logger's file handler
        log_file = None
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                log_file = handler.baseFilename
                break
        if log_file is None:
            # Fallback if no file handler found
            log_file = os.path.join(tempfile.gettempdir(), "uvicorn.log")

        # Start with uvicorn's default logging config
        config = copy.deepcopy(LOGGING_CONFIG)

        # Create a plain formatter without colors for logging to a log file
        config["formatters"]["plain"] = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }

        # Add a file handler using plain formatter appending to the same log
        # file as the root logger
        config["handlers"]["file"] = {
            "formatter": "plain",
            "class": "logging.FileHandler",
            "filename": log_file,
            "mode": "a",  # append to already existing log
            "encoding": "utf8",
        }

        # When using stdio transport, stdio is reserved for MCP JSON-RPC traffic.
        # Therefore redirect all uvicorn logging to stderr (by using uvicorn's
        # 'default' handler, see uvicorn.config.LOGGING_CONFIG for details) only
        # or stderr and the root logger log file.
        config["loggers"]["uvicorn"] = {"handlers": ["default"], "propagate": False}
        config["loggers"]["uvicorn.error"] = {
            "handlers": ["default", "file"],
            "level": logging.INFO if log_level == logging.DEBUG else logging.ERROR,
            "propagate": False,
        }
        config["loggers"]["uvicorn.access"] = {
            "handlers": ["default"],
            "level": logging.INFO if log_level == logging.DEBUG else logging.WARNING,
            "propagate": False,
        }

        # Avoid suppression of application logs by configuring root logger to use the Uvicorn log handlers
        config["root"] = {"handlers": ["default", "file"], "level": log_level}

        return config

    def start(self, port: int):
        """Start the viewer web server if there is not another one already running on the specified port
        and if the specified port is not in use by any other service running on this machine."""
        # Check inf another viewer web server instance is already running on the same port
        if self.is_already_running_on_same_port(port):
            raise DuplicateInstanceOnSamePortError(port)

        # Check if another service on this machine is already using the same port
        if self._is_port_in_use(port):
            raise PortInUseByAnotherServiceError(port)

        # Lock specified port for 10 min (600 seconds) - should be enough for typical usage
        port_locked_until = time.time() + WEB_SERVER_PORT_LOCK_SECS
        self._lock_port(port, port_locked_until)
        self._port = port

        # Set up viewer web server
        config = uvicorn.Config(
            app,
            host=LOCALHOST,
            port=self._port,
            loop="asyncio",
            log_config=self._get_log_config(),
        )
        self._web_server = uvicorn.Server(config)

        # Start viewer web server asynchronously in a background task
        logger.info(f"Starting viewer web server on http://{LOCALHOST}:{self._port}")

        # Create the task and store reference
        self._web_server_task = asyncio.create_task(self._web_server.serve())

    async def shutdown(self):
        """Gracefully shutdown the viewer web server with proper cleanup."""
        if self._web_server is not None:
            try:
                # Initiate graceful viewer web server shutdown
                logger.info("Shutting down viewer web server")
                self._web_server.should_exit = True
                await self._web_server.shutdown()
                self._web_server = None

                # Cancel the server task if it exists
                if not self._web_server_task.done():
                    self._web_server_task.cancel()

                # Remove viewer web server port from locked ports list
                if self._port is not None:
                    self._unlock_port(self._port)
                    self._port = None
            except Exception as e:
                logger.warning(f"Error during viewer web server shutdown: {e}")
            finally:
                logger.info("Viewer web server shutdown complete")
