from mcp_engine import mcp
from shell_wrapper import sw


@mcp.tool()
async def execut_command(
        command:str,
        cwd:str,
        run_in_background:bool=False,
        timeout:int|None=120,
    ):
    """Execute a shell command on the user's machine.

    Args:
        command: The shell command to execute (e.g. "ls -la", "npm install", "python script.py").
        cwd: Absolute path to the working directory where the command will run.
        run_in_background: If True, the command runs as a background process and returns
            its PID immediately instead of waiting for completion. Use this for long-running
            processes like servers, file watchers, or builds. You can then poll output with
            `read_output` and stop it with `kill_process`.
        timeout: Maximum seconds to wait for a foreground command to finish (default 120).
            Ignored when run_in_background is True. The process is killed if it exceeds this limit.

    Returns:
        For foreground commands: a string with stdout and stderr.
        For background commands: the integer PID of the spawned process.
    """
    return await sw.execut_command(
        command=command,
        cwd=cwd,
        run_in_background=run_in_background,
        timeout=timeout
    )