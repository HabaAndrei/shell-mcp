# Shell MCP

A **Model Context Protocol (MCP)** server that gives AI agents direct access to the host operating system shell. It exposes four tools over the MCP `stdio` transport so any MCP-compatible client (LangChain, Claude Desktop, etc.) can execute commands, manage background processes, and detect the host OS, all through a standardised interface.

## Why This Project Exists

This project was born from hands-on experience building coding agents. While developing my own coding agent, I realized that shell access is one of the most critical capabilities an agent can have, and getting it right is harder than it looks.

The key challenges I spent a lot of time solving:

- **Foreground vs. background execution**: some commands need to run and return immediately, others (like dev servers or long builds) need to keep running in the background while the agent continues working.
- **Timeouts and process lifecycle**: knowing when to wait, when to kill, and how to gracefully handle processes that hang or crash early.
- **Reading output from live processes**: giving the agent a way to check on background work without blocking.

These are problems every coding agent builder will face. The tool names and functionality here (`execut_command`, `read_output`, `kill_process`, `get_system`) represent what most real-world coding agents need. In your own project you'll likely have tools with the same purpose, adapted to your stack and language, but the architecture and the patterns stay the same.

**Think of this project as a reference implementation.** A working example of how to structure shell tools for a coding agent, how to handle the tricky parts (background processes, timeouts, graceful termination), and how to expose them over MCP so any client can use them. It's not a framework; it's a blueprint you can learn from and adapt.

## How It Was Built

### Stack

| Layer | Technology | Role |
|---|---|---|
| **MCP Framework** | [FastMCP](https://github.com/jlowin/fastmcp) (`mcp[cli]`) | Provides the MCP server skeleton, tool registration via `@mcp.tool()` decorators, and the `stdio` transport. This is the core that makes the tools discoverable by any MCP client. |
| **Python** | 3.13+ | The entire server is pure Python with no external runtime dependencies beyond the standard library and FastMCP. |
| **asyncio** | stdlib | Used for non-blocking foreground command execution (`asyncio.create_subprocess_shell`) and timeout handling (`asyncio.wait_for`). |
| **subprocess** | stdlib | Powers background process spawning (`subprocess.Popen`) and process inspection (`lsof`, `tasklist`). |
| **os / signal** | stdlib | Handles cross-platform process lifecycle: existence checks (`os.kill(pid, 0)`), graceful termination (`SIGTERM`), and force kill (`SIGKILL`). |
| **platform** | stdlib | OS detection so the agent knows whether it's talking to Linux, macOS, or Windows. |
| **logging** | stdlib | All logs go to `stderr` (never `stdout`, since MCP uses `stdout` for JSON-RPC communication). |
| **uv** | Package manager | Manages dependencies and runs the server (`uv run main.py`). |

### Architecture Decisions

1. **One tool per file** (`tools/` directory): each MCP tool lives in its own module with its own docstring. The `@mcp.tool()` decorator auto-registers it when imported. This keeps things clean and makes it easy to add or remove tools.

2. **ShellWrapper singleton**: all shell logic lives in a single class (`ShellWrapper`) instantiated once as `sw`. The tool files are thin wrappers that just call `sw.method()`. This separates the MCP layer from the actual shell logic, so you can test or reuse `ShellWrapper` independently.

3. **Foreground with timeout vs. background with PID**: instead of one generic "run" function, the server explicitly separates these two modes. Foreground commands block and return output. Background commands return a PID immediately, and the agent can poll or kill later. This distinction is critical for coding agents that need to start servers, run builds, or do long tasks.

4. **Graceful termination with fallback**: `kill_process` first sends `SIGTERM`, waits up to 1 second, then escalates to `SIGKILL`. This prevents zombie processes while still giving well-behaved processes a chance to clean up.

5. **Logging to stderr only**: MCP communicates over `stdout` using JSON-RPC. Any stray `print()` would corrupt the protocol. All logging is routed to `stderr` via Python's `logging` module.

## Tools

| Tool | Description |
|---|---|
| `get_system` | Returns the host OS name (`Linux`, `Darwin`, `Windows`) so the agent can pick the right shell syntax. |
| `execut_command` | Runs a shell command in the foreground (with timeout) **or** in the background (returns a PID). |
| `read_output` | Inspects a running background process and returns its current state and open resources. |
| `kill_process` | Gracefully terminates a background process (SIGTERM then SIGKILL fallback). |

## Project Structure

```
shell_mcp/
├── main.py              # Entry point, starts the MCP server on stdio
├── mcp_engine.py        # FastMCP server instance + instructions
├── shell_wrapper.py      # Core shell logic (run, background, read, kill)
├── logger.py            # Logging config (writes to stderr, not stdout)
├── tools/               # One file per MCP tool
│   ├── __init__.py
│   ├── execut_command.py
│   ├── get_system.py
│   ├── read_output.py
│   └── kill_process.py
├── pyproject.toml
└── use.py               # Example: LangChain agent using the MCP server
```

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)**, a fast Python package manager

## Installation

```bash
# Clone the repository
git clone <your-repo-url> shell_mcp
cd shell_mcp

# Install dependencies with uv
uv sync
```

---

## Integration Guide

### 1. LangChain + LangGraph Agent (with PostgreSQL memory)

This is a complete, copy-pasteable example. It connects to the Shell MCP server over `stdio`, creates a LangChain agent, and runs a conversational loop.

#### Step 1:Install dependencies in your client project

```bash
uv add langchain langchain-mcp-adapters langchain-openai langgraph-checkpoint-postgres python-dotenv
```

#### Step 2:Create a `.env` file

```env
OPENAI_API_KEY=sk-...
```

#### Step 3:Create `app.py`

```python
import os
import asyncio

from dotenv import load_dotenv
load_dotenv(override=True)

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# --- Config ---
DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres"
THREAD_ID = "1"
SHELL_MCP_DIR = "/absolute/path/to/shell_mcp"  # <-- change this


async def main():
    # 1. Connect to Postgres for conversation memory
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()

        # 2. Start the MCP server as a subprocess
        client = MultiServerMCPClient(
            {
                "shell_mcp": {
                    "transport": "stdio",
                    "command": "uv",
                    "args": ["run", "--directory", SHELL_MCP_DIR, "main.py"],
                },
            }
        )

        # 3. Fetch the tools the MCP server exposes
        tools = await client.get_tools()

        # 4. Create a LangChain agent with those tools
        agent = create_agent(
            "openai:gpt-4.1",
            tools,
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": THREAD_ID}}

        # 5. Chat loop
        print("Chat with Shell MCP (type 'exit' to quit)\n")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                break

            response = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            )
            print(f"AI: {response.get('messages')[-1].content}\n")


if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 4:Run it

```bash
uv run app.py
```

---

### 2. LangChain Agent without PostgreSQL (in-memory, simpler setup)

If you don't need persistent conversation memory, you can skip Postgres entirely:

```python
import os
import asyncio

from dotenv import load_dotenv
load_dotenv(override=True)

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

SHELL_MCP_DIR = "/absolute/path/to/shell_mcp"  # <-- change this


async def main():
    client = MultiServerMCPClient(
        {
            "shell_mcp": {
                "transport": "stdio",
                "command": "uv",
                "args": ["run", "--directory", SHELL_MCP_DIR, "main.py"],
            },
        }
    )

    tools = await client.get_tools()

    agent = create_agent("openai:gpt-4.1", tools)
    config = {"configurable": {"thread_id": "1"}}

    response = await agent.ainvoke(
        {"messages": [HumanMessage(content="What OS is this running on?")]},
        config=config,
    )
    print(f"AI: {response.get('messages')[-1].content}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 3. Claude Desktop Integration

Add this to your Claude Desktop MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "shell_mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/shell_mcp", "main.py"]
    }
  }
}
```

Restart Claude Desktop:the four shell tools will appear automatically.

---

## Example Prompts

Once integrated, you can ask your agent things like:

- *"What operating system is this?"*
- *"List all files in /Users/me/projects"*
- *"Run npm run dev in the background in /Users/me/app, wait a minute, then show me the output"*
- *"Kill process 12345"*

## License

MIT
