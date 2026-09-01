from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from datetime import datetime, timedelta
import secrets
import re
from pathlib import Path
import aiofiles  # type: ignore

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.file import File, FileType, FileStatus
from pydantic import BaseModel
from typing import Optional, Any

router = APIRouter()


def validate_upload_file(file_name: str, content_type: str | None, file_size: int) -> str:
    """Validate upload size and type before persisting the file."""
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed size",
        )

    extension = Path(file_name).suffix.lower().lstrip('.')
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension is required",
        )

    if extension not in {item.lower() for item in settings.ALLOWED_FILE_TYPES}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type is not allowed",
        )

    if content_type and content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is not allowed",
        )

    return extension


def build_storage_path(user_id: int, file_name: str, upload_root: str | None = None) -> Path:
    """Return a safe storage path for an uploaded file."""
    upload_root_path = Path(upload_root or settings.UPLOAD_DIR)
    upload_dir = upload_root_path / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file_name).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", original_name).strip("-.") or "upload"
    return upload_dir / safe_name


class FileUpdate(BaseModel):
    filename: Optional[str] = None
    metadata: Optional[dict] = None
    is_public: Optional[bool] = None


@router.get("/", response_model=None)
async def list_files(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[File]:
    """List all files for the current user."""
    result = await db.execute(
        select(File)
        .where(File.user_id == current_user_id)
        .where(File.deleted_at.is_(None))
        .order_by(File.created_at.desc())
    )
    files = result.scalars().all()
    return list(files)


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=None)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> File:
    """Upload a new file."""
    # Validate metadata before I/O, then stream to disk with a strict bound so
    # a forged Content-Length cannot make the API hold an arbitrary upload in
    # memory.
    validate_upload_file(file.filename or "", file.content_type, 0)

    # Determine file type
    file_type = FileType.OTHER
    if file.content_type:
        if file.content_type.startswith("image/"):
            file_type = FileType.IMAGE
        elif file.content_type.startswith("text/") or file.content_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            file_type = FileType.DOCUMENT
        elif file.content_type.startswith("audio/"):
            file_type = FileType.AUDIO
        elif file.content_type.startswith("video/"):
            file_type = FileType.VIDEO
        elif file.content_type in [
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
        ]:
            file_type = FileType.ARCHIVE
    
    safe_storage_path = build_storage_path(current_user_id, file.filename or "upload")
    storage_path = str(safe_storage_path)

    file_size = 0
    try:
        async with aiofiles.open(safe_storage_path, "wb") as target_file:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds the maximum allowed size",
                    )
                await target_file.write(chunk)
    except Exception:
        safe_storage_path.unlink(missing_ok=True)
        raise

    # Create file record
    file_record = File(
        user_id=current_user_id,
        filename=file.filename,
        original_filename=file.filename,
        file_type=file_type,
        mime_type=file.content_type or "application/octet-stream",
        status=FileStatus.COMPLETED,
        storage_path=storage_path,
        storage_provider="local",
        file_size=file_size,
        is_processed=True,
        processed_at=datetime.utcnow(),
    )
    
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    logger.info(f"File uploaded: {file_record.id}")
    
    return file_record


@router.get("/{file_id}", response_model=None)
async def get_file(
    file_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> File:
    """Get a specific file."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == current_user_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Update access count
    file.access_count += 1  # type: ignore[assignment]
    await db.commit()
    
    return file  # type: ignore[no-any-return]


@router.patch("/{file_id}", response_model=None)
async def update_file(
    file_id: int,
    file_data: FileUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> File:
    """Update a file."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == current_user_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Update fields
    update_data = file_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(file, field, value)
    
    await db.commit()
    await db.refresh(file)
    
    logger.info(f"File updated: {file_id}")
    
    return file  # type: ignore[no-any-return]


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Soft delete a file."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == current_user_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    file.deleted_at = datetime.utcnow()  # type: ignore[assignment]
    file.status = FileStatus.DELETED  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"File deleted: {file_id}")
    
    return {"message": "File deleted successfully"}


@router.post("/{file_id}/share")
async def share_file(
    file_id: int,
    max_accesses: Optional[int] = None,
    expires_in_days: int = 30,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Share a file and return share token."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == current_user_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Generate share token
    share_token = secrets.token_urlsafe(32)
    
    # Update file
    file.share_token = share_token  # type: ignore[assignment]
    file.share_expires_at = datetime.utcnow() + timedelta(days=expires_in_days)  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"File shared: {file_id}")
    
    return {"share_token": share_token, "expires_at": file.share_expires_at}
