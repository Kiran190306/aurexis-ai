"""
Terminal Agent - Safe shell command execution with permission checks.
"""
from typing import Dict, Optional, AsyncGenerator, Any
import asyncio
import subprocess
import os
import time
from datetime import datetime
from loguru import logger

from app.core.config import settings
from app.computer.base import (
    TerminalCommand,
    ExecutionResult,
    ComputerActionType,
    ExecutionStatus
)
from app.computer.permission_system import permission_system


class TerminalAgent:
    """Agent for safe terminal command execution."""
    
    def __init__(self) -> None:
        self.default_timeout = settings.COMPUTER_USE_COMMAND_TIMEOUT
        self.running_processes: Dict[str, Any] = {}
        self.command_history: list = []
        
        logger.info("TerminalAgent initialized")
    
    async def execute_command(
        self,
        command: str,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        stream_output: bool = False,
        user_id: int = 0
    ) -> ExecutionResult:
        """Execute shell command."""
        start_time = time.time()
        
        try:
            # Check permission (high risk)
            request = await permission_system.request_permission(
                ComputerActionType.TERMINAL_EXECUTE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"cmd_{int(time.time())}",
                    action_type=ComputerActionType.TERMINAL_EXECUTE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied (requires user approval)",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate working directory
            if working_directory and not self._is_path_allowed(working_directory):
                return ExecutionResult(
                    action_id=f"cmd_{int(time.time())}",
                    action_type=ComputerActionType.TERMINAL_EXECUTE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Working directory not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            # Prepare environment
            env = os.environ.copy()
            if environment:
                env.update(environment)
            
            # Set timeout
            cmd_timeout = timeout or self.default_timeout
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory,
                env=env
            )
            
            action_id = f"cmd_{int(time.time())}"
            self.running_processes[action_id] = process
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=cmd_timeout
                )
                
                output = stdout.decode('utf-8', errors='ignore')
                error = stderr.decode('utf-8', errors='ignore')
                
                success = process.returncode == 0
                
                # Add to history
                self.command_history.append({
                    "command": command,
                    "working_directory": working_directory,
                    "return_code": process.returncode,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Keep only last 100 commands
                if len(self.command_history) > 100:
                    self.command_history.pop(0)
                
                return ExecutionResult(
                    action_id=action_id,
                    action_type=ComputerActionType.TERMINAL_EXECUTE,
                    status=ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED,
                    success=success,
                    output=output,
                    error=error if error else None,
                    duration_seconds=time.time() - start_time,
                    metadata={
                        "return_code": process.returncode,
                        "command": command,
                        "working_directory": working_directory
                    }
                )
            
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                
                return ExecutionResult(
                    action_id=action_id,
                    action_type=ComputerActionType.TERMINAL_EXECUTE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error=f"Command timed out after {cmd_timeout} seconds",
                    duration_seconds=time.time() - start_time
                )
            
            finally:
                if action_id in self.running_processes:
                    del self.running_processes[action_id]
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return ExecutionResult(
                action_id=f"cmd_{int(time.time())}",
                action_type=ComputerActionType.TERMINAL_EXECUTE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def execute_command_stream(
        self,
        command: str,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        user_id: int = 0
    ) -> AsyncGenerator[str, None]:
        """Execute command with streaming output."""
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.TERMINAL_STREAM,
                user_id
            )
            
            if request.status != "approved":
                yield "Permission denied"
                return
            
            # Validate working directory
            if working_directory and not self._is_path_allowed(working_directory):
                yield "Working directory not allowed in sandbox"
                return
            
            # Prepare environment
            env = os.environ.copy()
            if environment:
                env.update(environment)
            
            # Set timeout
            cmd_timeout = timeout or self.default_timeout
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=working_directory,
                env=env
            )
            
            action_id = f"stream_{int(time.time())}"
            self.running_processes[action_id] = process
            
            try:
                if process.stdout:
                    while True:
                        line = await process.stdout.readline()
                        if not line:
                            break
                        yield line.decode('utf-8', errors='ignore').rstrip()
                
                await process.wait()
            
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                yield f"\nCommand timed out after {cmd_timeout} seconds"
            
            finally:
                if action_id in self.running_processes:
                    del self.running_processes[action_id]
        
        except Exception as e:
            logger.error(f"Stream execution failed: {e}")
            yield f"Error: {str(e)}"
    
    async def cancel_command(
        self,
        action_id: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Cancel a running command."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.TERMINAL_CANCEL,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=action_id,
                    action_type=ComputerActionType.TERMINAL_CANCEL,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if action_id not in self.running_processes:
                return ExecutionResult(
                    action_id=action_id,
                    action_type=ComputerActionType.TERMINAL_CANCEL,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Command not found or already completed",
                    duration_seconds=time.time() - start_time
                )
            
            process = self.running_processes[action_id]
            process.kill()
            await process.wait()
            
            del self.running_processes[action_id]
            
            return ExecutionResult(
                action_id=action_id,
                action_type=ComputerActionType.TERMINAL_CANCEL,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output="Command cancelled",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"Command cancellation failed: {e}")
            return ExecutionResult(
                action_id=action_id,
                action_type=ComputerActionType.TERMINAL_CANCEL,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def get_working_directory(self) -> str:
        """Get current working directory."""
        return os.getcwd()
    
    def set_working_directory(
        self,
        path: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Set working directory."""
        start_time = time.time()
        
        try:
            if not self._is_path_allowed(path):
                return ExecutionResult(
                    action_id=f"cwd_{int(time.time())}",
                    action_type=ComputerActionType.TERMINAL_EXECUTE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            os.chdir(path)
            
            return ExecutionResult(
                action_id=f"cwd_{int(time.time())}",
                action_type=ComputerActionType.TERMINAL_EXECUTE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Working directory set to: {path}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"Failed to set working directory: {e}")
            return ExecutionResult(
                action_id=f"cwd_{int(time.time())}",
                action_type=ComputerActionType.TERMINAL_EXECUTE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get current environment variables."""
        return dict(os.environ)
    
    def set_environment_variable(
        self,
        name: str,
        value: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Set environment variable."""
        start_time = time.time()
        
        try:
            os.environ[name] = value
            
            return ExecutionResult(
                action_id=f"env_{int(time.time())}",
                action_type=ComputerActionType.TERMINAL_EXECUTE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Environment variable {name} set",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"Failed to set environment variable: {e}")
            return ExecutionResult(
                action_id=f"env_{int(time.time())}",
                action_type=ComputerActionType.TERMINAL_EXECUTE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def get_command_history(self, limit: int = 50) -> list:
        """Get command execution history."""
        return self.command_history[-limit:]
    
    def get_running_commands(self) -> list:
        """Get list of currently running commands."""
        return [
            {
                "action_id": action_id,
                "pid": process.pid
            }
            for action_id, process in self.running_processes.items()
        ]
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is allowed in sandbox."""
        if not settings.COMPUTER_USE_SANDBOXED:
            return True
        
        from pathlib import Path
        path_obj = Path(path).resolve()
        
        for allowed_path in settings.COMPUTER_USE_ALLOWED_PATHS:
            allowed_obj = Path(allowed_path).resolve()
            try:
                path_obj.relative_to(allowed_obj)
                return True
            except ValueError:
                continue
        
        return False


# Global terminal agent instance
terminal_agent = TerminalAgent()
