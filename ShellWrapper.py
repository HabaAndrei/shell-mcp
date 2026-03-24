import asyncio
import threading
import os
import platform


# singleton thread safe
class ShellWrapper:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._processes = {}
        return cls._instance

    async def run_command(self, command: str, cwd:str, timeout=120) -> str:
        proc = None
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return f"stdout: {stdout.decode()}\nstderr: {stderr.decode()}"
        except asyncio.TimeoutError:
            if proc and proc.returncode is None:
                proc.kill()
                await proc.wait()
            return f"Command timed out after {timeout}s"
        except Exception as e:
            if proc and proc.returncode is None:
                proc.kill()
                await proc.wait()
            return str(e)

    async def run_command_in_background(self, command:str, cwd:str) -> int | str:
        try:
            env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
                cwd=cwd
            )
            proc._output_lines = []

            async def _reader():
                async for line in proc.stdout:
                    proc._output_lines.append(line.decode())

            asyncio.create_task(_reader())
            self._processes[proc.pid] = proc
            return proc.pid
        except Exception as e:
            return str(e)

    def read_output(self, pid:int, last=300) -> str:
        try:
            proc = self._processes.get(pid)
            if not proc:
                return f"No process with PID {pid}"
            lines = proc._output_lines[:last]
            del proc._output_lines[:last]
            return "".join(lines)
        except Exception as e:
            return str(e)

    async def kill_process(self, pid: int) -> str:
        try:
            proc = self._processes.get(pid)
            if not proc:
                return f"No process with PID {pid}"
            proc.kill()
            await proc.wait()
            del self._processes[pid]
            return f"Killed process {pid}"
        except Exception as e:
            return str(e)

    async def execut_command(
            self,
            command:str,
            cwd:str,
            run_in_background:bool=False,
            timeout:int|None=120,
        ):

        if run_in_background:
            return await self.run_command_in_background(command=command, cwd=cwd)

        return await self.run_command(
            command=command,
            cwd=cwd,
            timeout=timeout
        )

    def get_system(self):
        return platform.system()


sw = ShellWrapper()