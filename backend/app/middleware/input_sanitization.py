"""
Input sanitization utilities to prevent XSS and other injection attacks.
"""
import bleach
from typing import Optional
import re


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input by removing potentially dangerous content.
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length (truncates if longer)
    
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Remove HTML tags and dangerous characters
    # Allow basic formatting but strip scripts, styles, etc.
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']
    allowed_attributes = {}
    
    sanitized = bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove directory separators
    filename = filename.replace('/', '').replace('\\', '').replace('..', '')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    # Only allow alphanumeric, dots, dashes, underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    return filename
