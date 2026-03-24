from mcp_engine import mcp
from shell_wrapper import sw


@mcp.tool()
def read_output(pid:int, last:int=300):
    """Read information about a running background process.

    Uses OS-level tools (lsof on Unix, tasklist on Windows) to inspect the process
    and return its current state, including open file descriptors and resource usage.

    Args:
        pid: The process ID returned by `execut_command` when the background process was started.
        last: Maximum number of lines to return from the output (default 300).

    Returns:
        A string containing process information, or an error if the PID is not found.
    """
    return sw.read_output(pid=pid, last=last)