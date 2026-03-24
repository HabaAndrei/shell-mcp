from main import mcp
from ShellWrapper import sw

@mcp.tool()
def get_system():
    """Detect the host operating system.

    Call this first to determine which shell syntax and commands are available
    (e.g. bash on Linux/Darwin vs cmd/powershell on Windows).

    Returns:
        The OS name as a string: "Linux", "Darwin" (macOS), or "Windows".
    """
    return sw.get_system()