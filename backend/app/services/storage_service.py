"""
File storage service for handling uploads and downloads.
"""
import os
import aiofiles
import shutil
from typing import Optional
from fastapi import UploadFile
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.core.utils import ensure_directory_exists, sanitize_filename

logger = get_logger(__name__)


class StorageService:
    """Handles file storage operations."""
    
    def __init__(self):
        """Initialize storage service."""
        self.upload_dir = settings.upload_dir
        ensure_directory_exists(self.upload_dir)
        logger.info(f"StorageService initialized. Upload directory: {self.upload_dir}")
    
    async def save_uploaded_file(
        self,
        file: UploadFile,
        job_id: str,
        prefix: str = "original"
    ) -> tuple[str, int]:
        """
        Save uploaded file to storage.
        
        Args:
            file: Uploaded file
            job_id: Job identifier
            prefix: File prefix (default: "original")
            
        Returns:
            Tuple of (file_path, file_size)
            
        Raises:
            Exception: If save operation fails
        """
        try:
            # Sanitize filename
            original_filename = sanitize_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1]
            
            # Create new filename
            new_filename = f"{job_id}_{prefix}{file_extension}"
            file_path = os.path.join(self.upload_dir, new_filename)
            
            logger.info(f"Saving uploaded file: {new_filename}")
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
                file_size = len(content)
            
            logger.info(f"File saved successfully: {file_path} ({file_size} bytes)")
            return file_path, file_size
            
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}", exc_info=True)
            raise Exception(f"File save failed: {str(e)}")
    
    def get_file_path(self, job_id: str, prefix: str, extension: str) -> str:
        """
        Get file path for a specific job and prefix.
        
        Args:
            job_id: Job identifier
            prefix: File prefix
            extension: File extension (with dot)
            
        Returns:
            File path
        """
        filename = f"{job_id}_{prefix}{extension}"
        return os.path.join(self.upload_dir, filename)
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists, False otherwise
        """
        exists = os.path.exists(file_path)
        logger.debug(f"File exists check: {file_path} -> {exists}")
        return exists
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted, False if file didn't exist
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    def cleanup_job_files(self, job_id: str) -> int:
        """
        Delete all files associated with a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Number of files deleted
        """
        try:
            deleted_count = 0
            for filename in os.listdir(self.upload_dir):
                if filename.startswith(job_id):
                    file_path = os.path.join(self.upload_dir, filename)
                    if self.delete_file(file_path):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} files for job {job_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup failed for job {job_id}: {str(e)}")
            return 0