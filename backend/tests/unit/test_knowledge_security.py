"""
Unit tests for Knowledge Platform security
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.knowledge.security import (
    FileValidator,
    PermissionManager,
    EncryptionManager
)


class TestFileValidator:
    """Tests for FileValidator"""
    
    @pytest.fixture
    def validator(self):
        """Create a FileValidator instance"""
        return FileValidator()
    
    def test_validator_initialization(self, validator):
        """Test validator initialization"""
        assert len(validator.ALLOWED_MIME_TYPES) > 0
        assert len(validator.BLOCKED_EXTENSIONS) > 0
    
    def test_validate_file_blocked_extension(self, validator):
        """Test validation with blocked extension"""
        filename = "test.exe"
        content = b"test content"
        
        result = validator.validate_file(filename, content)
        
        assert result['valid'] is False
        assert any("Blocked file extension" in e for e in result['errors'])
    
    def test_validate_file_empty(self, validator):
        """Test validation with empty file"""
        filename = "test.pdf"
        content = b""
        
        result = validator.validate_file(filename, content)
        
        assert result['valid'] is False
        assert any("File is empty" in e for e in result['errors'])
    
    def test_validate_file_size_limit(self, validator):
        """Test validation with oversized file"""
        filename = "test.pdf"
        content = b"x" * (51 * 1024 * 1024)  # 51MB
        
        result = validator.validate_file(filename, content)
        
        assert result['valid'] is False
        assert any("exceeds" in e.lower() for e in result['errors'])


class TestPermissionManager:
    """Tests for PermissionManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a PermissionManager instance"""
        return PermissionManager()
    
    def test_check_document_access_owner(self, manager):
        """Test access check for document owner"""
        has_access = manager.check_document_access(
            user_id=1,
            document_user_id=1,
            is_public=False
        )
        
        assert has_access is True
    
    def test_check_document_access_public(self, manager):
        """Test access check for public document"""
        has_access = manager.check_document_access(
            user_id=2,
            document_user_id=1,
            is_public=True
        )
        
        assert has_access is True
    
    def test_check_document_access_denied(self, manager):
        """Test access check denied"""
        has_access = manager.check_document_access(
            user_id=2,
            document_user_id=1,
            is_public=False
        )
        
        assert has_access is False
    
    def test_check_search_access(self, manager):
        """Test search access check"""
        has_access = manager.check_search_access(
            user_id=1,
            document_user_id=1,
            is_public=False
        )
        
        assert has_access is True
    
    def test_filter_accessible_documents(self, manager):
        """Test filtering accessible documents"""
        documents = []
        for i in range(5):
            doc = Mock()
            doc.user_id = 1 if i % 2 == 0 else 2
            doc.is_public = False
            documents.append(doc)
        
        accessible = manager.filter_accessible_documents(user_id=1, documents=documents)
        
        assert len(accessible) <= len(documents)


class TestEncryptionManager:
    """Tests for EncryptionManager"""
    
    @pytest.fixture
    def manager(self):
        """Create an EncryptionManager instance"""
        return EncryptionManager()
    
    def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert manager.cipher is not None
    
    def test_encrypt_decrypt(self, manager):
        """Test encryption and decryption"""
        data = "sensitive data"
        
        encrypted = manager.encrypt(data)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == data
    
    def test_encrypt_file_content(self, manager):
        """Test file content encryption"""
        content = b"sensitive file content"
        
        encrypted = manager.encrypt_file_content(content)
        decrypted = manager.decrypt_file_content(encrypted)
        
        assert decrypted == content
    
    def test_encrypt_different_outputs(self, manager):
        """Test that encryption produces different outputs"""
        data = "test data"
        
        encrypted1 = manager.encrypt(data)
        encrypted2 = manager.encrypt(data)
        
        # Should be different due to IV
        assert encrypted1 != encrypted2
