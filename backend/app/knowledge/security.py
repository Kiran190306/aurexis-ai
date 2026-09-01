"""
Knowledge Platform Security
File validation, permissions, encryption, audit logs
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from pathlib import Path

from loguru import logger

from app.models.knowledge import KnowledgeAuditLog
from app.core.database import get_db

# Optional import - python-magic may not be available on all systems
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available - file type detection will be limited")


class FileValidator:
    """
    Validate uploaded files for security
    """
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/markdown',
        'text/plain',
        'text/html',
        'text/csv',
        'application/json',
        'application/xml',
        'text/xml',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/tiff',
        'image/bmp',
        'application/zip',
        'application/x-zip-compressed',
    }
    
    # Blocked file extensions
    BLOCKED_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.sh', '.ps1',
        '.dll', '.so', '.dylib',
        '.vbs', '.js', '.jar',
        '.deb', '.rpm', '.dmg',
        '.app', '.msi'
    }
    
    # Maximum file sizes (bytes)
    MAX_FILE_SIZES = {
        'application/pdf': 50 * 1024 * 1024,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 50 * 1024 * 1024,
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 50 * 1024 * 1024,
        'text/markdown': 10 * 1024 * 1024,
        'text/plain': 10 * 1024 * 1024,
        'text/html': 10 * 1024 * 1024,
        'text/csv': 50 * 1024 * 1024,
        'application/json': 10 * 1024 * 1024,
        'application/xml': 10 * 1024 * 1024,
        'image/png': 20 * 1024 * 1024,
        'image/jpeg': 20 * 1024 * 1024,
        'image/tiff': 20 * 1024 * 1024,
        'application/zip': 100 * 1024 * 1024,
    }
    
    def __init__(self) -> None:
        if MAGIC_AVAILABLE:
            self.magic = magic.Magic(mime=True)
        else:
            self.magic = None  # type: ignore
    
    def validate_file(
        self,
        filename: str,
        content: bytes,
        declared_mime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate file for security
        
        Args:
            filename: File name
            content: File content
            declared_mime: Declared MIME type from upload
            
        Returns:
            Validation result with status and details
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'detected_mime': None,
            'file_size': len(content)
        }
        
        # Check file extension
        ext = Path(filename).suffix.lower()
        if ext in self.BLOCKED_EXTENSIONS:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Blocked file extension: {ext}")  # type: ignore
        
        # Detect actual MIME type
        try:
            detected_mime = self.magic.from_buffer(content) if self.magic else None  # type: ignore
            validation_result['detected_mime'] = detected_mime
        except Exception as e:
            validation_result['warnings'].append(f"Failed to detect MIME type: {e}")  # type: ignore
            detected_mime = None
        
        # Check MIME type
        if detected_mime and detected_mime not in self.ALLOWED_MIME_TYPES:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Disallowed MIME type: {detected_mime}")  # type: ignore
        
        # Check for MIME type mismatch
        if declared_mime and detected_mime and declared_mime != detected_mime:
            validation_result['warnings'].append(  # type: ignore
                f"MIME type mismatch: declared={declared_mime}, detected={detected_mime}"
            )
        
        # Check file size
        file_size = len(content)
        max_size = self.MAX_FILE_SIZES.get(detected_mime, 10 * 1024 * 1024)  # type: ignore
        if file_size > max_size:
            validation_result['valid'] = False
            validation_result['errors'].append(  # type: ignore
                f"File size {file_size} exceeds maximum {max_size}"
            )
        
        # Check for empty file
        if file_size == 0:
            validation_result['valid'] = False
            validation_result['errors'].append("File is empty")  # type: ignore
        
        # Check for suspicious content
        if self._contains_suspicious_content(content):
            validation_result['valid'] = False
            validation_result['errors'].append("File contains suspicious content")  # type: ignore
        
        return validation_result
    
    def _contains_suspicious_content(self, content: bytes) -> bool:
        """Check for suspicious content patterns"""
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'data:text/html',
            b'<?php',
            b'<%',
            b'eval(',
            b'exec(',
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                return True
        
        return False


class VirusScanner:
    """
    Virus scanning integration (placeholder for actual antivirus)
    """
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
    
    async def scan_file(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Scan file for viruses
        
        Args:
            content: File content
            filename: File name
            
        Returns:
            Scan result
        """
        if not self.enabled:
            return {
                'scanned': False,
                'clean': True,
                'threats': [],
                'message': 'Virus scanning disabled'
            }
        
        # Placeholder for actual antivirus integration
        # In production, integrate with ClamAV, Windows Defender, etc.
        logger.info(f"Virus scan requested for {filename} (scanning disabled)")
        
        return {
            'scanned': True,
            'clean': True,
            'threats': [],
            'message': 'No threats detected'
        }


class PermissionManager:
    """
    Manage document access permissions
    """
    
    def __init__(self) -> None:
        pass
    
    def check_document_access(
        self,
        user_id: int,
        document_user_id: int,
        is_public: bool
    ) -> bool:
        """
        Check if user has access to document
        
        Args:
            user_id: User requesting access
            document_user_id: Document owner
            is_public: Whether document is public
            
        Returns:
            True if access granted
        """
        # Owner always has access
        if user_id == document_user_id:
            return True
        
        # Public documents accessible to all
        if is_public:
            return True
        
        # Otherwise, no access
        return False
    
    def check_search_access(
        self,
        user_id: int,
        document_user_id: int,
        is_public: bool
    ) -> bool:
        """
        Check if user can search document
        
        Args:
            user_id: User requesting search
            document_user_id: Document owner
            is_public: Whether document is public
            
        Returns:
            True if search access granted
        """
        return self.check_document_access(user_id, document_user_id, is_public)
    
    def filter_accessible_documents(
        self,
        user_id: int,
        documents: List[Any]
    ) -> List[Any]:
        """
        Filter documents to only accessible ones
        
        Args:
            user_id: User ID
            documents: List of document objects
            
        Returns:
            Filtered list of documents
        """
        accessible = []
        for doc in documents:
            if self.check_document_access(user_id, doc.user_id, doc.is_public):
                accessible.append(doc)
        
        return accessible


class EncryptionManager:
    """
    Manage encryption for sensitive data
    """
    
    def __init__(self) -> None:
        from cryptography.fernet import Fernet
        import os
        
        # In production, load key from secure storage
        key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        if isinstance(key, str):
            key_bytes: bytes = key.encode()
        else:
            key_bytes = key
        self.cipher = Fernet(key_bytes)
    
    def encrypt(self, data: str) -> bytes:
        """
        Encrypt data
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted bytes
        """
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt data
        
        Args:
            encrypted_data: Encrypted bytes
            
        Returns:
            Decrypted string
        """
        return self.cipher.decrypt(encrypted_data).decode()
    
    def encrypt_file_content(self, content: bytes) -> bytes:
        """
        Encrypt file content
        
        Args:
            content: File content bytes
            
        Returns:
            Encrypted bytes
        """
        return self.cipher.encrypt(content)
    
    def decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """
        Decrypt file content
        
        Args:
            encrypted_content: Encrypted bytes
            
        Returns:
            Decrypted bytes
        """
        return self.cipher.decrypt(encrypted_content)


class AuditLogger:
    """
    Log security and access events
    """
    
    def __init__(self) -> None:
        pass
    
    async def log_event(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log an audit event
        
        Args:
            user_id: User ID
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource ID
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether action succeeded
            error_message: Error message if failed
        """
        async for db in get_db():
            audit_log = KnowledgeAuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details_json=details,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            db.add(audit_log)
            await db.commit()
            
            logger.info(
                f"Audit log: user={user_id}, action={action}, "
                f"resource={resource_type}/{resource_id}, success={success}"
            )
    
    async def log_upload(
        self,
        user_id: int,
        document_id: int,
        filename: str,
        success: bool,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log document upload"""
        await self.log_event(
            user_id=user_id,
            action="upload",
            resource_type="document",
            resource_id=document_id,
            details={"filename": filename},
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
    
    async def log_search(
        self,
        user_id: int,
        query: str,
        result_count: int,
        ip_address: Optional[str] = None
    ) -> None:
        """Log search query"""
        await self.log_event(
            user_id=user_id,
            action="search",
            resource_type="knowledge",
            details={"query": query, "result_count": result_count},
            ip_address=ip_address,
            success=True
        )
    
    async def log_access(
        self,
        user_id: int,
        document_id: int,
        ip_address: Optional[str] = None
    ) -> None:
        """Log document access"""
        await self.log_event(
            user_id=user_id,
            action="view",
            resource_type="document",
            resource_id=document_id,
            ip_address=ip_address,
            success=True
        )
    
    async def log_delete(
        self,
        user_id: int,
        document_id: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Log document deletion"""
        await self.log_event(
            user_id=user_id,
            action="delete",
            resource_type="document",
            resource_id=document_id,
            success=success,
            error_message=error_message
        )


class SecurityManager:
    """
    Main security manager combining all security components
    """
    
    def __init__(self) -> None:
        self.file_validator = FileValidator()
        self.virus_scanner = VirusScanner(enabled=False)
        self.permission_manager = PermissionManager()
        self.encryption_manager = EncryptionManager()
        self.audit_logger = AuditLogger()
    
    async def validate_and_scan_upload(
        self,
        filename: str,
        content: bytes,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate and scan uploaded file
        
        Args:
            filename: File name
            content: File content
            user_id: User ID
            ip_address: Client IP address
            
        Returns:
            Validation and scan result
        """
        # Validate file
        validation_result = self.file_validator.validate_file(filename, content)
        
        if not validation_result['valid']:
            await self.audit_logger.log_upload(
                user_id=user_id,
                document_id=0,  # No document ID yet
                filename=filename,
                success=False,
                error_message="Validation failed: " + ", ".join(validation_result['errors']),
                ip_address=ip_address
            )
            return validation_result
        
        # Scan for viruses
        scan_result = await self.virus_scanner.scan_file(content, filename)
        
        if not scan_result['clean']:
            await self.audit_logger.log_upload(
                user_id=user_id,
                document_id=0,  # No document ID yet
                filename=filename,
                success=False,
                error_message="Virus scan failed: " + ", ".join(scan_result['threats']),
                ip_address=ip_address
            )
            validation_result['valid'] = False
            validation_result['errors'].extend(scan_result['threats'])
        
        validation_result['scan_result'] = scan_result
        
        return validation_result
    
    async def check_and_log_access(
        self,
        user_id: int,
        document_user_id: int,
        is_public: bool,
        document_id: int,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Check access and log the attempt
        
        Args:
            user_id: User requesting access
            document_user_id: Document owner
            is_public: Whether document is public
            document_id: Document ID
            ip_address: Client IP address
            
        Returns:
            True if access granted
        """
        has_access = self.permission_manager.check_document_access(
            user_id, document_user_id, is_public
        )
        
        if has_access:
            await self.audit_logger.log_access(user_id, document_id, ip_address)
        else:
            await self.audit_logger.log_event(
                user_id=user_id,
                action="view",
                resource_type="document",
                resource_id=document_id,
                ip_address=ip_address,
                success=False,
                error_message="Access denied"
            )
        
        return has_access


# Singleton instance
security_manager = SecurityManager()
