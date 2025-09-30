import argparse
import logging
import os
import sys
import tempfile

import fastmcp
from dotenv import load_dotenv

from . import LOCALHOST
from .mcp_server import VegaLiteViewerError, mcp
from .web_browser import web_browser

logger = logging.getLogger(__name__)


def cli():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Vega-Lite MCP Server and Viewer")

    # Server options
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port to run the viewer web server on (default: 8000)",
    )
    parser.add_argument(
        "--lazy-view",
        action="store_true",
        help="Open viewer app in browser lazily upon first visualization",
    )

    # Logging options
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--silent", action="store_true", help="Show only error messages")
    group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (can also be set through 'VEGALITE_VIEWER_DEBUG' environment variable)",
    )

    args = parser.parse_args()

    # Complementary options from environment (lower precedence than CLI args)
    load_dotenv(".env", override=True)

    if not args.debug and os.getenv("VEGALITE_VIEWER_DEBUG", ""):
        args.debug = os.getenv("VEGALITE_VIEWER_DEBUG", "").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        args.debug = True

    return args


def configure_logging(args):
    """Configure logging based on command line arguments."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if args.silent:
        log_level = logging.ERROR
    elif args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # When using stdio transport, stdio is reserved for MCP JSON-RPC traffic.
    # Therefore redirect logging to stderr and a log file.
    log_file = os.path.join(tempfile.gettempdir(), f"{__package__}.log")
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(log_file, mode="w"),  # truncate log file on startup
        ],
    )
    logger.info(f"Logging to stderr and file: {log_file}")


def main():
    args = cli()
    configure_logging(args)

    try:
        # Open browser unless lazy view is enabled
        if not args.lazy_view:
            logger.info(f"Opening viewer in browser at http://{LOCALHOST}:{args.port}")
            web_browser.open(args.port)

        # Hack: As we are always running this MCP server using stdio transport, we
        # leverage the HTTP transport-related MCP server settings to propagate
        # the viewer web server port
        fastmcp.settings.port = args.port

        # Start MCP server with stdio transport
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        # Graceful shutdown, suppress noisy logs resulting from asyncio.run task cancellation propagation
        pass
    except BaseExceptionGroup as e:
        # Required to properly handle exceptions raised in MCP server lifespan
        cause = next(iter(e.exceptions))
        if isinstance(cause, VegaLiteViewerError):
            logger.error(cause)
        else:
            # Unexpected internal error, include full stack trace
            logger.error(f"Internal error: {cause}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        # Unexpected internal error, include full stack trace
        logger.error(f"Internal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("MCP server shutdown complete")


if __name__ == "__main__":
    main()
