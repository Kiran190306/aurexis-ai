"""
Desktop Agent - Desktop automation with permission checks.
"""
from typing import Dict, Optional
import platform
import subprocess
import time
from loguru import logger

from app.core.config import settings
from app.computer.base import (
    DesktopAction,
    ExecutionResult,
    ComputerActionType,
    ExecutionStatus
)
from app.computer.permission_system import permission_system


class DesktopAgent:
    """Agent for desktop automation."""
    
    def __init__(self) -> None:
        self.platform = platform.system()
        self.clipboard_content: Optional[str] = None
        
        logger.info(f"DesktopAgent initialized (platform={self.platform})")
    
    async def launch_application(
        self,
        application: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Launch application."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DESKTOP_LAUNCH,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"launch_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_LAUNCH,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Platform-specific launch
            if self.platform == "Windows":
                subprocess.Popen(["start", "", application], shell=True)
            elif self.platform == "Darwin":  # macOS
                subprocess.Popen(["open", application])
            elif self.platform == "Linux":
                subprocess.Popen(["xdg-open", application])
            else:
                return ExecutionResult(
                    action_id=f"launch_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_LAUNCH,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error=f"Unsupported platform: {self.platform}",
                    duration_seconds=time.time() - start_time
                )
            
            return ExecutionResult(
                action_id=f"launch_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_LAUNCH,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Application launched: {application}",
                duration_seconds=time.time() - start_time,
                metadata={"application": application}
            )
        
        except Exception as e:
            logger.error(f"Application launch failed: {e}")
            return ExecutionResult(
                action_id=f"launch_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_LAUNCH,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def close_application(
        self,
        application: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Close application."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DESKTOP_CLOSE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"close_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLOSE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Platform-specific close
            if self.platform == "Windows":
                subprocess.Popen(["taskkill", "/IM", f"{application}.exe", "/F"])
            elif self.platform == "Darwin":  # macOS
                subprocess.Popen(["pkill", application])
            elif self.platform == "Linux":
                subprocess.Popen(["pkill", application])
            else:
                return ExecutionResult(
                    action_id=f"close_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLOSE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error=f"Unsupported platform: {self.platform}",
                    duration_seconds=time.time() - start_time
                )
            
            return ExecutionResult(
                action_id=f"close_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_CLOSE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Application closed: {application}",
                duration_seconds=time.time() - start_time,
                metadata={"application": application}
            )
        
        except Exception as e:
            logger.error(f"Application close failed: {e}")
            return ExecutionResult(
                action_id=f"close_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_CLOSE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def manage_window(
        self,
        action: str,
        window_title: Optional[str] = None,
        user_id: int = 0
    ) -> ExecutionResult:
        """Manage window (minimize, maximize, restore)."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DESKTOP_WINDOW,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"window_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_WINDOW,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Window management requires platform-specific libraries
            # For now, return not implemented
            return ExecutionResult(
                action_id=f"window_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_WINDOW,
                status=ExecutionStatus.FAILED,
                success=False,
                error="Window management requires platform-specific libraries (pywin32, AppKit, etc.)",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"Window management failed: {e}")
            return ExecutionResult(
                action_id=f"window_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_WINDOW,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def get_clipboard(
        self,
        user_id: int = 0
    ) -> ExecutionResult:
        """Get clipboard content."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DESKTOP_CLIPBOARD,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"clipboard_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Get clipboard content
            try:
                import pyperclip
                content = pyperclip.paste()
                self.clipboard_content = content
                
                return ExecutionResult(
                    action_id=f"clipboard_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                    status=ExecutionStatus.COMPLETED,
                    success=True,
                    output=content,
                    duration_seconds=time.time() - start_time
                )
            
            except ImportError:
                return ExecutionResult(
                    action_id=f"clipboard_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="pyperclip library required for clipboard access",
                    duration_seconds=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Clipboard read failed: {e}")
            return ExecutionResult(
                action_id=f"clipboard_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def set_clipboard(
        self,
        content: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Set clipboard content."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DESKTOP_CLIPBOARD,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"clipboard_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Set clipboard content
            try:
                import pyperclip
                pyperclip.copy(content)
                self.clipboard_content = content
                
                return ExecutionResult(
                    action_id=f"clipboard_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                    status=ExecutionStatus.COMPLETED,
                    success=True,
                    output="Clipboard updated",
                    duration_seconds=time.time() - start_time
                )
            
            except ImportError:
                return ExecutionResult(
                    action_id=f"clipboard_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="pyperclip library required for clipboard access",
                    duration_seconds=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Clipboard write failed: {e}")
            return ExecutionResult(
                action_id=f"clipboard_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_CLIPBOARD,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def send_notification(
        self,
        title: str,
        message: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Send desktop notification."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DESKTOP_NOTIFICATION,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"notify_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_NOTIFICATION,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Send notification
            try:
                import plyer
                plyer.notification.notify(
                    title=title,
                    message=message,
                    app_name="Jarvis AI"
                )
                
                return ExecutionResult(
                    action_id=f"notify_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_NOTIFICATION,
                    status=ExecutionStatus.COMPLETED,
                    success=True,
                    output="Notification sent",
                    duration_seconds=time.time() - start_time,
                    metadata={"title": title}
                )
            
            except ImportError:
                return ExecutionResult(
                    action_id=f"notify_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_NOTIFICATION,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="plyer library required for notifications",
                    duration_seconds=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return ExecutionResult(
                action_id=f"notify_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_NOTIFICATION,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def capture_screen(
        self,
        user_id: int = 0
    ) -> ExecutionResult:
        """Capture screen screenshot."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.DESKTOP_CAPTURE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"capture_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CAPTURE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Capture screenshot
            try:
                import mss
                import mss.tools as mss_tools
                
                with mss.mss() as sct:
                    monitor = sct.monitors[0]
                    screenshot = sct.grab(monitor)
                    
                    # Save screenshot
                    screenshot_path = f"./data/screenshots/desktop_{int(time.time())}.png"
                    mss_tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
                
                return ExecutionResult(
                    action_id=f"capture_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CAPTURE,
                    status=ExecutionStatus.COMPLETED,
                    success=True,
                    output=f"Screenshot saved to: {screenshot_path}",
                    duration_seconds=time.time() - start_time,
                    metadata={"screenshot_path": screenshot_path}
                )
            
            except ImportError:
                return ExecutionResult(
                    action_id=f"capture_{int(time.time())}",
                    action_type=ComputerActionType.DESKTOP_CAPTURE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="mss library required for screen capture",
                    duration_seconds=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return ExecutionResult(
                action_id=f"capture_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_CAPTURE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def get_platform(self) -> str:
        """Get current platform."""
        return self.platform
    
    def get_running_applications(self) -> ExecutionResult:
        """Get list of running applications."""
        start_time = time.time()
        
        try:
            applications = []
            
            if self.platform == "Windows":
                try:
                    import psutil
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name']:
                            applications.append(proc.info['name'])
                except ImportError:
                    return ExecutionResult(
                        action_id=f"apps_{int(time.time())}",
                        action_type=ComputerActionType.DESKTOP_WINDOW,
                        status=ExecutionStatus.FAILED,
                        success=False,
                        error="psutil library required",
                        duration_seconds=time.time() - start_time
                    )
            else:
                # For Unix-like systems
                try:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')[1:]
                    for line in lines:
                        parts = line.split()
                        if len(parts) > 10:
                            applications.append(' '.join(parts[10:]))
                except Exception:
                    pass
            
            return ExecutionResult(
                action_id=f"apps_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_WINDOW,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=str(applications),
                duration_seconds=time.time() - start_time,
                metadata={"count": len(applications)}
            )
        
        except Exception as e:
            logger.error(f"Failed to get running applications: {e}")
            return ExecutionResult(
                action_id=f"apps_{int(time.time())}",
                action_type=ComputerActionType.DESKTOP_WINDOW,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )


# Global desktop agent instance
desktop_agent = DesktopAgent()
