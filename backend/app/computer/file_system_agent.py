"""
File System Agent - Safe file system operations with permission checks.
"""
from typing import Dict, List, Optional, AsyncGenerator, Any
from pathlib import Path
import os
import shutil
import zipfile
import time
from loguru import logger

from app.core.config import settings
from app.computer.base import (
    FileOperation,
    ExecutionResult,
    ComputerActionType,
    ExecutionStatus
)
from app.computer.permission_system import permission_system


class FileSystemAgent:
    """Agent for safe file system operations."""
    
    def __init__(self) -> None:
        self.max_depth = settings.FILE_SYSTEM_MAX_DEPTH
        self.max_results = settings.FILE_SYSTEM_MAX_RESULTS
        self.max_file_size = settings.COMPUTER_USE_MAX_FILE_SIZE
        
        logger.info("FileSystemAgent initialized")
    
    async def browse_directory(
        self,
        path: str,
        depth: int = 1,
        user_id: int = 0
    ) -> ExecutionResult:
        """Browse directory contents."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DIRECTORY_BROWSE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"browse_{int(time.time())}",
                    action_type=ComputerActionType.DIRECTORY_BROWSE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate path
            if not self._is_path_allowed(path):
                return ExecutionResult(
                    action_id=f"browse_{int(time.time())}",
                    action_type=ComputerActionType.DIRECTORY_BROWSE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            dir_path = Path(path)
            if not dir_path.exists():
                return ExecutionResult(
                    action_id=f"browse_{int(time.time())}",
                    action_type=ComputerActionType.DIRECTORY_BROWSE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Directory does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            if not dir_path.is_dir():
                return ExecutionResult(
                    action_id=f"browse_{int(time.time())}",
                    action_type=ComputerActionType.DIRECTORY_BROWSE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path is not a directory",
                    duration_seconds=time.time() - start_time
                )
            
            # Browse directory
            contents: List[Dict[str, Any]] = []
            self._browse_recursive(dir_path, depth, 0, contents)
            
            return ExecutionResult(
                action_id=f"browse_{int(time.time())}",
                action_type=ComputerActionType.DIRECTORY_BROWSE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=str(contents),
                duration_seconds=time.time() - start_time,
                metadata={"count": len(contents), "path": path}
            )
        
        except Exception as e:
            logger.error(f"Directory browse failed: {e}")
            return ExecutionResult(
                action_id=f"browse_{int(time.time())}",
                action_type=ComputerActionType.DIRECTORY_BROWSE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _browse_recursive(
        self,
        path: Path,
        max_depth: int,
        current_depth: int,
        results: List[Dict]
    ) -> None:
        """Recursively browse directory."""
        if current_depth > max_depth or len(results) >= self.max_results:
            return
        
        try:
            for item in path.iterdir():
                if len(results) >= self.max_results:
                    break
                
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                }
                results.append(item_info)
                
                if item.is_dir() and current_depth < max_depth:
                    self._browse_recursive(item, max_depth, current_depth + 1, results)
        
        except PermissionError:
            pass
    
    async def read_file(
        self,
        path: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Read file contents."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_READ,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"read_{int(time.time())}",
                    action_type=ComputerActionType.FILE_READ,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate path
            if not self._is_path_allowed(path):
                return ExecutionResult(
                    action_id=f"read_{int(time.time())}",
                    action_type=ComputerActionType.FILE_READ,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            file_path = Path(path)
            if not file_path.exists():
                return ExecutionResult(
                    action_id=f"read_{int(time.time())}",
                    action_type=ComputerActionType.FILE_READ,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="File does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            if not file_path.is_file():
                return ExecutionResult(
                    action_id=f"read_{int(time.time())}",
                    action_type=ComputerActionType.FILE_READ,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path is not a file",
                    duration_seconds=time.time() - start_time
                )
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return ExecutionResult(
                    action_id=f"read_{int(time.time())}",
                    action_type=ComputerActionType.FILE_READ,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error=f"File too large ({file_size} bytes, max {self.max_file_size})",
                    duration_seconds=time.time() - start_time
                )
            
            # Read file
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            return ExecutionResult(
                action_id=f"read_{int(time.time())}",
                action_type=ComputerActionType.FILE_READ,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=content,
                duration_seconds=time.time() - start_time,
                metadata={"path": path, "size": file_size}
            )
        
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return ExecutionResult(
                action_id=f"read_{int(time.time())}",
                action_type=ComputerActionType.FILE_READ,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def write_file(
        self,
        path: str,
        content: str,
        overwrite: bool = False,
        user_id: int = 0
    ) -> ExecutionResult:
        """Write content to file."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_WRITE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"write_{int(time.time())}",
                    action_type=ComputerActionType.FILE_WRITE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate path
            if not self._is_path_allowed(path):
                return ExecutionResult(
                    action_id=f"write_{int(time.time())}",
                    action_type=ComputerActionType.FILE_WRITE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            file_path = Path(path)
            
            # Check if file exists and overwrite is False
            if file_path.exists() and not overwrite:
                return ExecutionResult(
                    action_id=f"write_{int(time.time())}",
                    action_type=ComputerActionType.FILE_WRITE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="File already exists (use overwrite=True)",
                    duration_seconds=time.time() - start_time
                )
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_path.write_text(content, encoding='utf-8')
            
            return ExecutionResult(
                action_id=f"write_{int(time.time())}",
                action_type=ComputerActionType.FILE_WRITE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"File written: {path}",
                duration_seconds=time.time() - start_time,
                metadata={"path": path, "size": len(content)}
            )
        
        except Exception as e:
            logger.error(f"File write failed: {e}")
            return ExecutionResult(
                action_id=f"write_{int(time.time())}",
                action_type=ComputerActionType.FILE_WRITE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def delete_file(
        self,
        path: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Delete file (requires confirmation)."""
        start_time = time.time()
        
        try:
            # Check permission (high risk)
            request = await permission_system.request_permission(
                ComputerActionType.FILE_DELETE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"delete_{int(time.time())}",
                    action_type=ComputerActionType.FILE_DELETE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied (requires user confirmation)",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate path
            if not self._is_path_allowed(path):
                return ExecutionResult(
                    action_id=f"delete_{int(time.time())}",
                    action_type=ComputerActionType.FILE_DELETE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            file_path = Path(path)
            if not file_path.exists():
                return ExecutionResult(
                    action_id=f"delete_{int(time.time())}",
                    action_type=ComputerActionType.FILE_DELETE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="File does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Delete file
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            
            return ExecutionResult(
                action_id=f"delete_{int(time.time())}",
                action_type=ComputerActionType.FILE_DELETE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Deleted: {path}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"File delete failed: {e}")
            return ExecutionResult(
                action_id=f"delete_{int(time.time())}",
                action_type=ComputerActionType.FILE_DELETE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def rename_file(
        self,
        source: str,
        target: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Rename file or directory."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_RENAME,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"rename_{int(time.time())}",
                    action_type=ComputerActionType.FILE_RENAME,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate paths
            if not self._is_path_allowed(source) or not self._is_path_allowed(target):
                return ExecutionResult(
                    action_id=f"rename_{int(time.time())}",
                    action_type=ComputerActionType.FILE_RENAME,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            source_path = Path(source)
            target_path = Path(target)
            
            if not source_path.exists():
                return ExecutionResult(
                    action_id=f"rename_{int(time.time())}",
                    action_type=ComputerActionType.FILE_RENAME,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Source does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Rename
            source_path.rename(target_path)
            
            return ExecutionResult(
                action_id=f"rename_{int(time.time())}",
                action_type=ComputerActionType.FILE_RENAME,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Renamed {source} to {target}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"File rename failed: {e}")
            return ExecutionResult(
                action_id=f"rename_{int(time.time())}",
                action_type=ComputerActionType.FILE_RENAME,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def move_file(
        self,
        source: str,
        target: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Move file or directory."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_MOVE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"move_{int(time.time())}",
                    action_type=ComputerActionType.FILE_MOVE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate paths
            if not self._is_path_allowed(source) or not self._is_path_allowed(target):
                return ExecutionResult(
                    action_id=f"move_{int(time.time())}",
                    action_type=ComputerActionType.FILE_MOVE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            source_path = Path(source)
            target_path = Path(target)
            
            if not source_path.exists():
                return ExecutionResult(
                    action_id=f"move_{int(time.time())}",
                    action_type=ComputerActionType.FILE_MOVE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Source does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Move
            shutil.move(str(source_path), str(target_path))
            
            return ExecutionResult(
                action_id=f"move_{int(time.time())}",
                action_type=ComputerActionType.FILE_MOVE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Moved {source} to {target}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"File move failed: {e}")
            return ExecutionResult(
                action_id=f"move_{int(time.time())}",
                action_type=ComputerActionType.FILE_MOVE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def copy_file(
        self,
        source: str,
        target: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Copy file or directory."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_COPY,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"copy_{int(time.time())}",
                    action_type=ComputerActionType.FILE_COPY,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate paths
            if not self._is_path_allowed(source) or not self._is_path_allowed(target):
                return ExecutionResult(
                    action_id=f"copy_{int(time.time())}",
                    action_type=ComputerActionType.FILE_COPY,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            source_path = Path(source)
            target_path = Path(target)
            
            if not source_path.exists():
                return ExecutionResult(
                    action_id=f"copy_{int(time.time())}",
                    action_type=ComputerActionType.FILE_COPY,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Source does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Copy
            if source_path.is_file():
                shutil.copy2(source_path, target_path)
            elif source_path.is_dir():
                shutil.copytree(source_path, target_path)
            
            return ExecutionResult(
                action_id=f"copy_{int(time.time())}",
                action_type=ComputerActionType.FILE_COPY,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Copied {source} to {target}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"File copy failed: {e}")
            return ExecutionResult(
                action_id=f"copy_{int(time.time())}",
                action_type=ComputerActionType.FILE_COPY,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def search_files(
        self,
        path: str,
        pattern: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Search for files matching pattern."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_SEARCH,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"search_{int(time.time())}",
                    action_type=ComputerActionType.FILE_SEARCH,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate path
            if not self._is_path_allowed(path):
                return ExecutionResult(
                    action_id=f"search_{int(time.time())}",
                    action_type=ComputerActionType.FILE_SEARCH,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            search_path = Path(path)
            if not search_path.exists():
                return ExecutionResult(
                    action_id=f"search_{int(time.time())}",
                    action_type=ComputerActionType.FILE_SEARCH,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Search path does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Search
            results: List[Dict[str, str]] = []
            for item in search_path.rglob(pattern):
                if len(results) >= self.max_results:
                    break
                results.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file"
                })
            
            return ExecutionResult(
                action_id=f"search_{int(time.time())}",
                action_type=ComputerActionType.FILE_SEARCH,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=str(results),
                duration_seconds=time.time() - start_time,
                metadata={"count": len(results), "pattern": pattern}
            )
        
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return ExecutionResult(
                action_id=f"search_{int(time.time())}",
                action_type=ComputerActionType.FILE_SEARCH,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def create_archive(
        self,
        source: str,
        target: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Create ZIP archive."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_ARCHIVE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"archive_{int(time.time())}",
                    action_type=ComputerActionType.FILE_ARCHIVE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate paths
            if not self._is_path_allowed(source) or not self._is_path_allowed(target):
                return ExecutionResult(
                    action_id=f"archive_{int(time.time())}",
                    action_type=ComputerActionType.FILE_ARCHIVE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            source_path = Path(source)
            if not source_path.exists():
                return ExecutionResult(
                    action_id=f"archive_{int(time.time())}",
                    action_type=ComputerActionType.FILE_ARCHIVE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Source does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Create archive
            with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if source_path.is_file():
                    zipf.write(source_path, source_path.name)
                elif source_path.is_dir():
                    for item in source_path.rglob('*'):
                        zipf.write(item, item.relative_to(source_path.parent))
            
            return ExecutionResult(
                action_id=f"archive_{int(time.time())}",
                action_type=ComputerActionType.FILE_ARCHIVE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Archive created: {target}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"Archive creation failed: {e}")
            return ExecutionResult(
                action_id=f"archive_{int(time.time())}",
                action_type=ComputerActionType.FILE_ARCHIVE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def extract_archive(
        self,
        source: str,
        target: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Extract ZIP archive."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.FILE_EXTRACT,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"extract_{int(time.time())}",
                    action_type=ComputerActionType.FILE_EXTRACT,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Validate paths
            if not self._is_path_allowed(source) or not self._is_path_allowed(target):
                return ExecutionResult(
                    action_id=f"extract_{int(time.time())}",
                    action_type=ComputerActionType.FILE_EXTRACT,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Path not allowed in sandbox",
                    duration_seconds=time.time() - start_time
                )
            
            source_path = Path(source)
            if not source_path.exists():
                return ExecutionResult(
                    action_id=f"extract_{int(time.time())}",
                    action_type=ComputerActionType.FILE_EXTRACT,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Archive does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Extract
            with zipfile.ZipFile(source, 'r') as zipf:
                zipf.extractall(target)
            
            return ExecutionResult(
                action_id=f"extract_{int(time.time())}",
                action_type=ComputerActionType.FILE_EXTRACT,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Archive extracted to: {target}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"Archive extraction failed: {e}")
            return ExecutionResult(
                action_id=f"extract_{int(time.time())}",
                action_type=ComputerActionType.FILE_EXTRACT,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is allowed in sandbox."""
        if not settings.COMPUTER_USE_SANDBOXED:
            return True
        
        path_obj = Path(path).resolve()
        
        for allowed_path in settings.COMPUTER_USE_ALLOWED_PATHS:
            allowed_obj = Path(allowed_path).resolve()
            try:
                path_obj.relative_to(allowed_obj)
                return True
            except ValueError:
                continue
        
        return False


# Global file system agent instance
file_system_agent = FileSystemAgent()
