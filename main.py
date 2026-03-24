from mcp_engine import mcp
import tools  # Import registers all tools via @mcp.tool() decorators
from logger import log_info

log_info("Server started — waiting for connections on stdio")
mcp.run(transport="stdio")