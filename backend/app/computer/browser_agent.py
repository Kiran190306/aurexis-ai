"""
Browser Automation Agent - Playwright-based browser automation with permission checks.
"""
from typing import Dict, Optional, List, Any, TYPE_CHECKING
import asyncio
import time
from loguru import logger

from app.core.config import settings
from app.computer.base import (
    BrowserAction,
    ExecutionResult,
    ComputerActionType,
    ExecutionStatus
)
from app.computer.permission_system import permission_system

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext


class BrowserAgent:
    """Agent for browser automation using Playwright."""
    
    def __init__(self) -> None:
        self.headless = settings.PLAYWRIGHT_HEADLESS
        self.browser_type = settings.PLAYWRIGHT_BROWSER
        self.timeout = settings.COMPUTER_USE_BROWSER_TIMEOUT
        
        self.browser: Optional["Browser"] = None
        self.context: Optional["BrowserContext"] = None
        self.pages: Dict[str, Any] = {}
        
        logger.info(f"BrowserAgent initialized (browser={self.browser_type}, headless={self.headless})")
    
    async def initialize(self) -> ExecutionResult:
        """Initialize browser instance."""
        start_time = time.time()
        
        try:
            from playwright.async_api import async_playwright as pw
            
            self.playwright = await pw().start()
            
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unsupported browser: {self.browser_type}")
            
            if self.browser:
                self.context = await self.browser.new_context()
            
            logger.info("Browser initialized successfully")
            
            return ExecutionResult(
                action_id=f"init_{int(time.time())}",
                action_type=ComputerActionType.BROWSER_OPEN,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output="Browser initialized successfully",
                duration_seconds=time.time() - start_time
            )
        
        except ImportError:
            logger.error("Playwright not installed - Browser automation not available")
            return ExecutionResult(
                action_id=f"init_{int(time.time())}",
                action_type=ComputerActionType.BROWSER_OPEN,
                status=ExecutionStatus.FAILED,
                success=False,
                error="Playwright required for browser automation",
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return ExecutionResult(
                action_id=f"init_{int(time.time())}",
                action_type=ComputerActionType.BROWSER_OPEN,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def shutdown(self) -> ExecutionResult:
        """Shutdown browser instance."""
        start_time = time.time()
        
        try:
            if self.context:
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            self.pages.clear()
            logger.info("Browser shutdown complete")
            
            return ExecutionResult(
                action_id=f"shutdown_{int(time.time())}",
                action_type=ComputerActionType.BROWSER_CLOSE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output="Browser shutdown complete",
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Browser shutdown failed: {e}")
            return ExecutionResult(
                action_id=f"shutdown_{int(time.time())}",
                action_type=ComputerActionType.BROWSER_CLOSE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def open_browser(
        self,
        url: Optional[str] = None,
        user_id: int = 0
    ) -> ExecutionResult:
        """Open browser and optionally navigate to URL."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_OPEN,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"browser_{int(time.time())}",
                    action_type=ComputerActionType.BROWSER_OPEN,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            # Initialize if not already
            if not self.browser:
                await self.initialize()
            
            # Create new page
            if self.context:
                page = await self.context.new_page()
                page_id = f"page_{int(time.time())}"
                self.pages[page_id] = page
            else:
                raise ValueError("Browser context not initialized")
            
            if url:
                await page.goto(url, timeout=self.timeout * 1000)
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_OPEN,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Browser opened (page_id: {page_id})",
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "url": url}
            )
        
        except Exception as e:
            logger.error(f"Browser open failed: {e}")
            return ExecutionResult(
                action_id=f"browser_{int(time.time())}",
                action_type=ComputerActionType.BROWSER_OPEN,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def navigate(
        self,
        page_id: str,
        url: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Navigate to URL."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_NAVIGATE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_NAVIGATE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id not in self.pages:
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_NAVIGATE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Page not found",
                    duration_seconds=time.time() - start_time
                )
            
            page = self.pages[page_id]
            await page.goto(url, timeout=self.timeout * 1000)
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_NAVIGATE,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Navigated to {url}",
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "url": url}
            )
        
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_NAVIGATE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def click_element(
        self,
        page_id: str,
        selector: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Click element on page."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_CLICK,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_CLICK,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id not in self.pages:
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_CLICK,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Page not found",
                    duration_seconds=time.time() - start_time
                )
            
            page = self.pages[page_id]
            await page.click(selector, timeout=self.timeout * 1000)
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_CLICK,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Clicked element: {selector}",
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "selector": selector}
            )
        
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_CLICK,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def fill_form(
        self,
        page_id: str,
        selector: str,
        value: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Fill form field."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_FILL,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_FILL,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id not in self.pages:
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_FILL,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Page not found",
                    duration_seconds=time.time() - start_time
                )
            
            page = self.pages[page_id]
            await page.fill(selector, value, timeout=self.timeout * 1000)
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_FILL,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Filled {selector} with value",
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "selector": selector}
            )
        
        except Exception as e:
            logger.error(f"Fill failed: {e}")
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_FILL,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def extract_content(
        self,
        page_id: str,
        selector: Optional[str] = None,
        user_id: int = 0
    ) -> ExecutionResult:
        """Extract content from page."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_EXTRACT,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_EXTRACT,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id not in self.pages:
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_EXTRACT,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Page not found",
                    duration_seconds=time.time() - start_time
                )
            
            page = self.pages[page_id]
            
            if selector:
                content = await page.inner_text(selector, timeout=self.timeout * 1000)
            else:
                content = await page.inner_text('body', timeout=self.timeout * 1000)
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_EXTRACT,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=content,
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "selector": selector}
            )
        
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_EXTRACT,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def download_file(
        self,
        page_id: str,
        url: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Download file from URL."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_DOWNLOAD,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_DOWNLOAD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id not in self.pages:
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_DOWNLOAD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Page not found",
                    duration_seconds=time.time() - start_time
                )
            
            page = self.pages[page_id]
            
            # Setup download handler
            async with page.expect_download(timeout=self.timeout * 1000) as download_info:
                await page.goto(url, timeout=self.timeout * 1000)
            
            download = await download_info.value
            download_path = await download.path()
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_DOWNLOAD,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"File downloaded to: {download_path}",
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "download_path": download_path}
            )
        
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_DOWNLOAD,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def upload_file(
        self,
        page_id: str,
        selector: str,
        file_path: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Upload file via file input."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_UPLOAD,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_UPLOAD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id not in self.pages:
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_UPLOAD,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Page not found",
                    duration_seconds=time.time() - start_time
                )
            
            page = self.pages[page_id]
            file_chooser = await page.query_selector(selector)
            await file_chooser.set_input_files(file_path)
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_UPLOAD,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"File uploaded: {file_path}",
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "selector": selector, "file_path": file_path}
            )
        
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_UPLOAD,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def take_screenshot(
        self,
        page_id: str,
        user_id: int = 0
    ) -> ExecutionResult:
        """Take screenshot of page."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_SCREENSHOT,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_SCREENSHOT,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id not in self.pages:
                return ExecutionResult(
                    action_id=page_id,
                    action_type=ComputerActionType.BROWSER_SCREENSHOT,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Page not found",
                    duration_seconds=time.time() - start_time
                )
            
            page = self.pages[page_id]
            screenshot_path = f"./data/screenshots/screenshot_{int(time.time())}.png"
            
            await page.screenshot(path=screenshot_path, timeout=self.timeout * 1000)
            
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_SCREENSHOT,
                status=ExecutionStatus.COMPLETED,
                success=True,
                output=f"Screenshot saved to: {screenshot_path}",
                duration_seconds=time.time() - start_time,
                metadata={"page_id": page_id, "screenshot_path": screenshot_path}
            )
        
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ExecutionResult(
                action_id=page_id,
                action_type=ComputerActionType.BROWSER_SCREENSHOT,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def close_browser(
        self,
        page_id: Optional[str] = None,
        user_id: int = 0
    ) -> ExecutionResult:
        """Close browser page or entire browser."""
        start_time = time.time()
        
        try:
            # Check permission
            request = await permission_system.request_permission(
                ComputerActionType.BROWSER_CLOSE,
                user_id
            )
            
            if request.status != "approved":
                return ExecutionResult(
                    action_id=f"close_{int(time.time())}",
                    action_type=ComputerActionType.BROWSER_CLOSE,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error="Permission denied",
                    duration_seconds=time.time() - start_time
                )
            
            if page_id:
                # Close specific page
                if page_id in self.pages:
                    await self.pages[page_id].close()
                    del self.pages[page_id]
                    return ExecutionResult(
                        action_id=page_id,
                        action_type=ComputerActionType.BROWSER_CLOSE,
                        status=ExecutionStatus.COMPLETED,
                        success=True,
                        output=f"Page {page_id} closed",
                        duration_seconds=time.time() - start_time
                    )
                else:
                    return ExecutionResult(
                        action_id=page_id,
                        action_type=ComputerActionType.BROWSER_CLOSE,
                        status=ExecutionStatus.FAILED,
                        success=False,
                        error="Page not found",
                        duration_seconds=time.time() - start_time
                    )
            else:
                # Close all pages and browser
                await self.shutdown()
                return ExecutionResult(
                    action_id=f"close_{int(time.time())}",
                    action_type=ComputerActionType.BROWSER_CLOSE,
                    status=ExecutionStatus.COMPLETED,
                    success=True,
                    output="Browser closed",
                    duration_seconds=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Browser close failed: {e}")
            return ExecutionResult(
                action_id=f"close_{int(time.time())}",
                action_type=ComputerActionType.BROWSER_CLOSE,
                status=ExecutionStatus.FAILED,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def get_active_pages(self) -> List[str]:
        """Get list of active page IDs."""
        return list(self.pages.keys())


# Global browser agent instance
browser_agent = BrowserAgent()
