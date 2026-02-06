"""
Shared utility functions used across the application.
"""
import os
import uuid
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from app.config.logging_config import get_logger

logger = get_logger(__name__)


def generate_job_id() -> str:
    """
    Generate a unique job identifier.
    
    Returns:
        Unique job ID string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    job_id = f"job_{timestamp}_{unique_id}"
    logger.debug(f"Generated job ID: {job_id}")
    return job_id


def ensure_directory_exists(directory: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        directory: Directory path to create
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {str(e)}")
        raise


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension without dot
    """
    return os.path.splitext(filename)[1][1:].lower()


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Validate if file extension is allowed.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions
        
    Returns:
        True if valid, False otherwise
    """
    ext = get_file_extension(filename)
    is_valid = ext in allowed_extensions
    logger.debug(f"File '{filename}' extension validation: {is_valid}")
    return is_valid


def get_trace_info() -> str:
    """
    Get current execution trace information.
    
    Returns:
        Trace string in format "filename:function:line"
    """
    try:
        tb = traceback.extract_stack()[-2]
        return f"{tb.filename}:{tb.name}:{tb.lineno}"
    except Exception:
        return "unknown:unknown:0"


def build_response(
    status: str,
    message: str,
    data: Optional[Any] = None,
    trace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build standardized API response.
    
    Args:
        status: 'success' or 'error'
        message: Human-readable message
        data: Response data
        trace: Error trace location
        
    Returns:
        Standardized response dictionary
    """
    response = {
        "status": status,
        "message": message,
        "data": data,
        "trace": trace or get_trace_info()
    }
    return response


def calculate_percentage(obtained: float, total: float) -> float:
    """
    Calculate percentage score.
    
    Args:
        obtained: Marks obtained
        total: Total marks
        
    Returns:
        Percentage score
    """
    if total == 0:
        return 0.0
    return round((obtained / total) * 100, 2)


def get_grade_from_percentage(percentage: float) -> str:
    """
    Get letter grade from percentage score.
    
    Args:
        percentage: Percentage score
        
    Returns:
        Letter grade
    """
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove unsafe characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    sanitized = filename
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized