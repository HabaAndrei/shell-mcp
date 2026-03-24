import asyncio
import subprocess
import threading
import os
import platform
from logger import log_info, log_error, log_debug
import signal
import time


class ShellWrapper:

    async def run_command(self, command: str, cwd:str, timeout=120) -> str:
        proc = None
        log_info(f"Running command: {command} | cwd: {cwd} | timeout: {timeout}s")
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            log_debug(f"Command finished: {command} | exit code: {proc.returncode}")
            return f"stdout: {stdout.decode()}\nstderr: {stderr.decode()}"
        except asyncio.TimeoutError:
            if proc and proc.returncode is None:
                proc.kill()
                await proc.wait()
            log_error(f"Command timed out after {timeout}s: {command}")
            return f"Command timed out after {timeout}s"
        except Exception as e:
            if proc and proc.returncode is None:
                proc.kill()
                await proc.wait()
            log_error(f"Command failed: {command} | error: {e}")
            return str(e)

    async def run_command_in_background(self, command:str, cwd:str) -> int | str:
        log_info(f"Starting background command: {command} | cwd: {cwd}")
        try:
            env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=cwd,
            )
            pid = proc.pid

            # Wait briefly to detect early crashes
            await asyncio.sleep(3)
            ret = proc.poll()
            if ret is not None:
                output = proc.stdout.read().decode()
                log_error(f"Background process exited immediately: PID {pid} | exit code: {ret}")
                return f"Process exited immediately with code {ret}\n{output}"

            log_info(f"Background process started: PID {pid} | command: {command}")
            return pid
        except Exception as e:
            log_error(f"Failed to start background command: {command} | error: {e}")
            return str(e)


    def read_output(self, pid:int, last:int=300) -> str:
        log_info(f"Reading output for PID {pid} | last {last} lines")
        system = platform.system()
        try:
            if system == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/V"],
                    capture_output=True, text=True, timeout=5
                )
            else:
                result = subprocess.run(
                    ["lsof", "-p", str(pid)],
                    capture_output=True, text=True, timeout=5
                )

            if result.returncode != 0:
                log_error(f"Process {pid} not found or not accessible")
                return f"Process {pid} not found or not accessible"

            lines = result.stdout.splitlines()
            log_debug(f"Read {len(lines)} lines from PID {pid}, returning last {last}")
            return "\n".join(lines[-last:])

        except FileNotFoundError:
            log_error(f"Required command not available on {system}")
            return f"Required command not available on {system}"
        except Exception as e:
            log_error(f"Error reading output for PID {pid}: {e}")
            return f"Error: {e}"

    def kill_process(self, pid: int) -> str:
        log_info(f"Killing process: PID {pid}")
        system = platform.system()

        # Check if process exists
        if system == "Windows":
            check = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True
            )
            if str(pid) not in check.stdout:
                log_error(f"Process {pid} does not exist")
                return f"Process {pid} does not exist"
        else:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                log_error(f"Process {pid} does not exist")
                return f"Process {pid} does not exist"
            except PermissionError:
                log_error(f"Permission denied for process {pid}")
                return f"Permission denied for process {pid}"

        # Graceful termination
        if system == "Windows":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                log_info(f"Process {pid} terminated gracefully (Windows)")
                return f"Process {pid} terminated"
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except PermissionError:
                log_error(f"Permission denied to terminate process {pid}")
                return f"Permission denied to terminate process {pid}"

        # Wait up to 1 second
        for _ in range(10):
            time.sleep(0.1)
            if system == "Windows":
                check = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True, text=True
                )
                if str(pid) not in check.stdout:
                    log_info(f"Process {pid} terminated after SIGTERM")
                    return f"Process {pid} terminated"
            else:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    log_info(f"Process {pid} terminated after SIGTERM")
                    return f"Process {pid} terminated"

        # Force kill
        log_info(f"Graceful termination failed for PID {pid}, force killing")
        if system == "Windows":
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                log_info(f"Process {pid} force killed")
                return f"Process {pid} force killed"
            log_error(f"Failed to kill process {pid}: {result.stderr}")
            return f"Failed to kill process {pid}: {result.stderr}"
        else:
            try:
                os.kill(pid, signal.SIGKILL)
                log_info(f"Process {pid} force killed (SIGKILL)")
                return f"Process {pid} force killed"
            except PermissionError:
                log_error(f"Permission denied to kill process {pid}")
                return f"Permission denied to kill process {pid}"
            except Exception as e:
                log_error(f"Error killing process {pid}: {e}")
                return f"Error killing process {pid}: {e}"

    async def execut_command(
            self,
            command:str,
            cwd:str,
            run_in_background:bool=False,
            timeout:int|None=120,
        ):
        log_info(f"Executing command: {command} | cwd: {cwd} | background: {run_in_background} | timeout: {timeout}s")

        if run_in_background:
            return await self.run_command_in_background(command=command, cwd=cwd)

        return await self.run_command(
            command=command,
            cwd=cwd,
            timeout=timeout
        )

    def get_system(self):
        system = platform.system()
        log_debug(f"Detected system: {system}")
        return system


sw = ShellWrapper()