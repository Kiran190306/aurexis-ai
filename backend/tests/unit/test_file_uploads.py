import pytest
from unittest.mock import AsyncMock

from app.api.v1.endpoints.files import validate_upload_file, build_storage_path


def test_validate_upload_file_rejects_large_files():
    with pytest.raises(Exception):
        validate_upload_file("test.pdf", "application/pdf", 200 * 1024 * 1024)


def test_validate_upload_file_rejects_unsupported_extension():
    with pytest.raises(Exception):
        validate_upload_file("test.exe", "application/octet-stream", 1024)


def test_build_storage_path_sanitizes_names():
    path = build_storage_path(7, "../../evil.pdf")
    assert path.parent.name == "7"
    assert path.name == "evil.pdf"
