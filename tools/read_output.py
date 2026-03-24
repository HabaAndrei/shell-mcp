from mcp_engine import mcp
from ShellWrapper import sw


@mcp.tool()
async def read_output(pid:int, last:int=300):
    """Read new output lines from a running background process.

    Lines are consumed: each call returns only lines that have not been read before.
    Call this repeatedly to stream incremental output from long-running commands
    (e.g. a dev server, a build, or a test suite).

    Args:
        pid: The process ID returned by `execut_command` when the background process was started.
        last: Maximum number of buffered lines to return in this call (default 300).

    Returns:
        A string containing the new output lines, or an error if the PID is unknown.
    """
    return sw.read_output(pid=pid, last=last)