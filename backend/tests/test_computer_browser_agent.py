"""
Unit tests for Computer Use Browser Automation Agent.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from app.computer.browser_agent import browser_agent
from app.computer.base import ExecutionResult, ExecutionStatus, ComputerActionType


@pytest.fixture
def mock_permission_system():
    """Mock the permission system."""
    with patch('app.computer.browser_agent.permission_system') as mock:
        # Mock check_permission to return True by default
        mock.check_permission = AsyncMock(return_value=True)
        
        # Mock request_permission to return an object with status attribute
        mock_request = MagicMock()
        mock_request.status = "approved"
        mock_request.request_id = "test_request_id"
        mock.request_permission = AsyncMock(return_value=mock_request)
        
        yield mock


@pytest.fixture
def mock_playwright():
    """Mock Playwright browser."""
    with patch('playwright.async_api.async_playwright') as mock:
        # Mock the async_playwright() call to return a context manager
        mock_context_manager = MagicMock()
        mock.return_value = mock_context_manager
        
        # Mock the start() method to return an awaitable that returns the playwright instance
        mock_playwright_instance = MagicMock()
        mock_start_result = AsyncMock(return_value=mock_playwright_instance)
        mock_context_manager.start = mock_start_result
        
        # Mock browser and context
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        # Make all browser methods async
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        # Make page methods async
        mock_page.goto = AsyncMock()
        mock_page.click = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_page.close = AsyncMock()
        mock_page.query_selector = AsyncMock()
        mock_page.inner_text = AsyncMock(return_value="Test content")
        
        # Mock file operations
        mock_file_chooser = MagicMock()
        mock_file_chooser.set_input_files = AsyncMock()
        
        # Mock download as async context manager
        # The code does: async with page.expect_download() as download_info:
        #              download = await download_info.value
        #              download_path = await download.path()
        mock_download = MagicMock()
        mock_download.path = AsyncMock(return_value="/path/to/file.pdf")
        
        # Create a class that mimics the download info context manager
        class MockDownloadInfo:
            def __init__(self):
                self._download = mock_download
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
            
            @property
            def value(self):
                async def get_download():
                    return self._download
                return get_download()
        
        mock_download_info = MockDownloadInfo()
        
        # Make expect_download return the async context manager directly
        mock_page.expect_download = MagicMock(return_value=mock_download_info)
        
        # Reset query_selector for regular use
        mock_page.query_selector = AsyncMock(return_value=mock_file_chooser)
        
        # Make browser close async
        mock_browser.close = AsyncMock()
        mock_context.close = AsyncMock()
        
        # Make playwright stop async
        mock_playwright_instance.stop = AsyncMock()
        
        yield mock_playwright_instance, mock_browser, mock_page


class TestBrowserAgentInitialization:
    """Test BrowserAgent initialization."""

    def test_initialization(self):
        """Test that BrowserAgent initializes correctly."""
        assert browser_agent is not None
        assert hasattr(browser_agent, 'open_browser')
        assert hasattr(browser_agent, 'navigate')
        assert hasattr(browser_agent, 'click_element')


class TestInitialize:
    """Test browser initialization."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_permission_system, mock_playwright):
        """Test successful browser initialization."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"

            result = await browser_agent.initialize()

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED


class TestShutdown:
    """Test browser shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_success(self, mock_permission_system, mock_playwright):
        """Test successful browser shutdown."""
        mock_pw, mock_browser, mock_page = mock_playwright

        # First initialize
        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

        # Then shutdown
        result = await browser_agent.shutdown()

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED


class TestOpenBrowser:
    """Test browser opening functionality."""

    @pytest.mark.asyncio
    async def test_open_browser_without_url(self, mock_permission_system, mock_playwright):
        """Test opening browser without URL."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            result = await browser_agent.open_browser(None, user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        assert result.metadata is not None
        assert "page_id" in result.metadata

    @pytest.mark.asyncio
    async def test_open_browser_with_url(self, mock_permission_system, mock_playwright):
        """Test opening browser with URL."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            result = await browser_agent.open_browser("https://example.com", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_page.goto.assert_called_once()


class TestNavigate:
    """Test browser navigation functionality."""

    @pytest.mark.asyncio
    async def test_navigate_success(self, mock_permission_system, mock_playwright):
        """Test successful navigation."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser(None, user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.navigate(page_id, "https://example.com", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_page.goto.assert_called_with("https://example.com", timeout=60000)

    @pytest.mark.asyncio
    async def test_navigate_invalid_page_id(self, mock_permission_system, mock_playwright):
        """Test navigation with invalid page ID."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            result = await browser_agent.navigate("invalid_id", "https://example.com", user_id=1)

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "not found" in result.error.lower()


class TestClickElement:
    """Test element clicking functionality."""

    @pytest.mark.asyncio
    async def test_click_element_success(self, mock_permission_system, mock_playwright):
        """Test successful element clicking."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.click_element(page_id, "#button", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_page.click.assert_called_once()


class TestFillForm:
    """Test form filling functionality."""

    @pytest.mark.asyncio
    async def test_fill_form_success(self, mock_permission_system, mock_playwright):
        """Test successful form filling."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.fill_form(page_id, "#input", "test value", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_page.fill.assert_called_once()


class TestExtractContent:
    """Test content extraction functionality."""

    @pytest.mark.asyncio
    async def test_extract_content_full_page(self, mock_permission_system, mock_playwright):
        """Test extracting full page content."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.extract_content(page_id, None, user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_extract_content_with_selector(self, mock_permission_system, mock_playwright):
        """Test extracting content with selector."""
        mock_pw, mock_browser, mock_page = mock_playwright
        mock_page.query_selector = MagicMock()
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(return_value="Selected content")
        mock_page.query_selector.return_value = mock_element

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.extract_content(page_id, "#content", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True


class TestDownloadFile:
    """Test file download functionality."""

    @pytest.mark.asyncio
    async def test_download_file_success(self, mock_permission_system, mock_playwright):
        """Test successful file download."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            mock_settings.PLAYWRIGHT_DOWNLOAD_PATH = "./data/playwright"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.download_file(page_id, "https://example.com/file.pdf", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True


class TestUploadFile:
    """Test file upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, mock_permission_system, mock_playwright):
        """Test successful file upload."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.upload_file(page_id, "#file-input", "/path/to/file.txt", user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True


class TestTakeScreenshot:
    """Test screenshot functionality."""

    @pytest.mark.asyncio
    async def test_take_screenshot_success(self, mock_permission_system, mock_playwright):
        """Test successful screenshot capture."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.take_screenshot(page_id, user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_page.screenshot.assert_called_once()


class TestCloseBrowser:
    """Test browser closing functionality."""

    @pytest.mark.asyncio
    async def test_close_page_success(self, mock_permission_system, mock_playwright):
        """Test successful page closing."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            open_result = await browser_agent.open_browser("https://example.com", user_id=1)
            page_id = open_result.metadata["page_id"]

            result = await browser_agent.close_browser(page_id, user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_all_pages(self, mock_permission_system, mock_playwright):
        """Test closing all pages."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            await browser_agent.initialize()

            result = await browser_agent.close_browser(None, user_id=1)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        mock_browser.close.assert_called_once()


class TestGetActivePages:
    """Test getting active pages."""

    def test_get_active_pages_empty(self):
        """Test getting active pages when none exist."""
        pages = browser_agent.get_active_pages()
        assert pages == []

    def test_get_active_pages_with_pages(self, mock_permission_system, mock_playwright):
        """Test getting active pages with pages."""
        mock_pw, mock_browser, mock_page = mock_playwright

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"
            # Manually add a page
            browser_agent.pages = {"page1": mock_page}

            pages = browser_agent.get_active_pages()

        assert len(pages) == 1
        assert "page1" in pages


class TestPermissionDenied:
    """Test permission denial scenarios."""

    @pytest.mark.asyncio
    async def test_open_browser_permission_denied(self, mock_permission_system, mock_playwright):
        """Test opening browser with permission denied."""
        mock_permission_system.check_permission.return_value = False
        mock_permission_system.request_permission.return_value = MagicMock(status="denied")

        with patch('app.computer.browser_agent.settings') as mock_settings:
            mock_settings.PLAYWRIGHT_HEADLESS = True
            mock_settings.PLAYWRIGHT_BROWSER = "chromium"

            result = await browser_agent.open_browser("https://example.com", user_id=1)

        assert result.status == ExecutionStatus.FAILED
        assert result.success is False
        assert "Permission denied" in result.error
