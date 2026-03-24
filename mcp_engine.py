from mcp.server.fastmcp import FastMCP

name = "shell_mcp"

# Initialize FastMCP server
mcp = FastMCP(
    name=name,
    instructions="""
    Shell MCP — a Model Context Protocol server that gives you direct access to the
    user's operating system shell. You can execute arbitrary shell commands (foreground
    or background), read streaming output from long-running background processes,
    kill background processes, and detect the host OS.

    Typical workflow:
    1. Call `get_system` to discover the OS (Linux, Darwin, Windows) so you can
        pick the right shell syntax and commands.
    2. Use `execut_command` to run any shell command. For short-lived commands the
        full stdout/stderr is returned directly. For long-running commands (servers,
        builds, watchers) set `run_in_background=True` — you will receive a PID.
    3. Poll a background process with `read_output` using its PID to stream new
        output lines incrementally.
    4. When a background process is no longer needed, terminate it with `kill_process`.

    Always provide an absolute `cwd` path when executing commands. Prefer short
    timeouts for commands that should finish quickly and background mode for anything
    that may run indefinitely.
    """
)
