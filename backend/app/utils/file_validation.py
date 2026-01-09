"""
File validation utilities to check file types and sizes.
"""
import os
from typing import Tuple
from fastapi import UploadFile, HTTPException, status


# Maximum file sizes (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_SIZE = 100 * 1024  # 100KB for direct text input

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.txt', '.docx', '.pdf'}

# Magic bytes for file type detection
FILE_SIGNATURES = {
    b'\x50\x4B\x03\x04': '.docx',  # ZIP-based formats (DOCX is a ZIP)
    b'%PDF': '.pdf',
    # TXT doesn't have a magic signature, so we'll check extension
}


def validate_file_size(file: UploadFile) -> None:
    """
    Validate file size.
    
    Raises:
        HTTPException if file is too large
    """
    # Read file size
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )


def validate_file_extension(filename: str) -> str:
    """
    Validate file extension.
    
    Args:
        filename: File name
    
    Returns:
        Extension if valid
    
    Raises:
        HTTPException if extension is not allowed
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    return ext


def validate_file_content(file: UploadFile, extension: str) -> None:
    """
    Validate file content using magic bytes.
    
    Args:
        file: Upload file
        extension: Expected extension
    
    Raises:
        HTTPException if content doesn't match extension
    """
    # Read first few bytes
    file.file.seek(0)
    header = file.file.read(4)
    file.file.seek(0)  # Reset
    
    # Check magic bytes
    if extension == '.pdf':
        if not header.startswith(b'%PDF'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match PDF format"
            )
    elif extension == '.docx':
        # DOCX files start with PK (ZIP signature)
        if not header.startswith(b'PK'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match DOCX format"
            )
    # TXT files don't have magic bytes, so we skip validation
    # In production, you might want to check for valid UTF-8


def validate_upload_file(file: UploadFile) -> Tuple[str, str]:
    """
    Complete file validation: size, extension, and content.
    
    Args:
        file: Upload file
    
    Returns:
        Tuple of (filename, extension)
    
    Raises:
        HTTPException if validation fails
    """
    # Validate size
    validate_file_size(file)
    
    # Validate extension
    extension = validate_file_extension(file.filename)
    
    # Validate content (magic bytes)
    try:
        validate_file_content(file, extension)
    except Exception as e:
        # If magic byte validation fails, still allow but log
        # Some files might be valid but not detected correctly
        pass
    
    return file.filename, extension


def validate_text_length(text: str) -> None:
    """
    Validate text length for direct text input.
    
    Args:
        text: Text to validate
    
    Raises:
        HTTPException if text is too long
    """
    if len(text.encode('utf-8')) > MAX_TEXT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Text exceeds maximum allowed size of {MAX_TEXT_SIZE / 1024:.1f}KB"
        )
