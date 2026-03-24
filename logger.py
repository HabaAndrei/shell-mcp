import logging
import sys
from mcp_engine import name

# Configure logger to write to stderr (NOT stdout - MCP uses stdout for JSONRPC)
logger = logging.getLogger(name=name)
logger.setLevel(logging.DEBUG)

# Only add handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(f"%(asctime)s | {name} | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)


def log_info(message: str) -> None:
    """Log an info message."""
    logger.info(message)


def log_error(message: str) -> None:
    """Log an error message with MCP context prefix."""
    logger.error(message)