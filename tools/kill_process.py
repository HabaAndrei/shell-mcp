
from main import mcp
from ShellWrapper import sw


@mcp.tool()
async def kill_process(pid: int):
    """Terminate a background process that was previously started with `execut_command(run_in_background=True)`.

    Args:
        pid: The process ID returned by `execut_command` when the background process was started.

    Returns:
        A confirmation message that the process was killed, or an error if the PID is unknown.
    """
    return await sw.kill_process(pid=pid)