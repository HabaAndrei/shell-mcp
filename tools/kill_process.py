from mcp_engine import mcp
from shell_wrapper import sw


@mcp.tool()
def kill_process(pid: int):
    """Terminate a background process that was previously started with `execut_command(run_in_background=True)`.

    Args:
        pid: The process ID returned by `execut_command` when the background process was started.

    Returns:
        A confirmation message that the process was killed, or an error if the PID is unknown.
    """
    return sw.kill_process(pid=pid)