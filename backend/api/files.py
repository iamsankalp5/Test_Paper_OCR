"""
Saved Files API - View and reprocess previously uploaded files.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.auth import get_current_user
from app.models.user import UserInDB
from app.core.utils import build_response
from app.config.logging_config import get_logger
import os

logger = get_logger(__name__)
router = APIRouter()

@router.get("/")
async def get_saved_files(
    current_user: UserInDB = Depends(get_current_user),
    db: DatabaseService = Depends(get_database)
):
    """
    Get all saved files for current user.
    
    Returns:
        List of previously uploaded files with metadata
    """
    try:
        logger.info(f"Fetching saved files for user: {current_user.user_id}")
        
        query = {}
        if current_user.role == "student":
            query["student_id"] = current_user.user_id
        
        jobs = await db.get_jobs_by_query(query, limit=100, sort_by="created_at", sort_order=-1)
        
        saved_files = []
        for job in jobs:
            file_path = job.get("original_image_path") or job.get("preprocessed_image_path")
            
            file_size = 0
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            
            saved_files.append({
                "job_id": job["job_id"],
                "file_name": os.path.basename(file_path) if file_path else "Unknown",
                "file_path": file_path,
                "file_size": file_size,  
                "student_name": job.get("student_name", "Unknown"),
                "student_id": job.get("student_id", "Unknown"),
                "exam_name": job.get("exam_name", "Unknown Exam"),
                "subject": job.get("subject", "Unknown"),
                "uploaded_at": job.get("created_at"),
                "state": job.get("state", "unknown"),
                "percentage": job.get("percentage", 0)
            })
        
        logger.info(f"Found {len(saved_files)} saved files")
        
        return build_response(
            status="success",
            message=f"Found {len(saved_files)} saved file(s)",
            data={"files": saved_files, "total": len(saved_files)}
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch saved files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch saved files: {str(e)}")


@router.post("/reprocess/{job_id}")
async def reprocess_file(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: DatabaseService = Depends(get_database)
):
    """
    Reprocess an existing uploaded file.
    
    Args:
        job_id: ID of the job to reprocess
        
    Returns:
        New job ID for reprocessing
    """
    try:
        logger.info(f"Reprocessing file for job: {job_id}")
        
        # Get original job
        original_job = await db.get_job(job_id)
        if not original_job:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check permission
        if current_user.role == "student" and original_job.get("student_id") != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to reprocess this file")
        
        # Check if file exists
        file_path = original_job.get("original_image_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Original file not found on server")
        
        from app.core.workflow_manager import WorkflowManager
        from fastapi import UploadFile
        from datetime import datetime
        from io import BytesIO
        
        # Read the file
        with open(file_path, 'rb') as f:
            file_content = f.read()
            file_name = os.path.basename(file_path)
        
        # Create a proper UploadFile mock
        class ReprocessUploadFile:
            def __init__(self, filename: str, content: bytes):
                self.filename = filename
                self.content_type = "image/jpeg" if filename.lower().endswith(('.jpg', '.jpeg')) else "application/pdf"
                self._content = content
                self._file = BytesIO(content)
            
            async def read(self, size: int = -1):
                return self._file.read(size)
            
            async def seek(self, offset: int):
                return self._file.seek(offset)
            
            async def close(self):
                return self._file.close()
        
        # Create mock file
        reprocess_file_obj = ReprocessUploadFile(file_name, file_content)
        
        workflow_manager = WorkflowManager()
        
        # Execute autonomous pipeline
        result = await workflow_manager.execute_autonomous_pipeline(
            file=reprocess_file_obj,
            student_name=original_job.get("student_name"),
            student_id=original_job.get("student_id"),
            reference_id=original_job.get("reference_id"),
            exam_name=original_job.get("exam_name"),
            subject=original_job.get("subject"),
            total_marks=original_job.get("total_marks", 100)
        )
        
        logger.info(f"Reprocessing complete. New job ID: {result['job_id']}")
        
        return build_response(
            status="success",
            message="File reprocessing started",
            data={"new_job_id": result["job_id"]}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reprocess file: {str(e)}")

@router.delete("/{job_id}")
async def delete_saved_file(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: DatabaseService = Depends(get_database)
):
    """
    Delete a saved file and its associated job data.
    
    Args:
        job_id: Job ID to delete
        
    Returns:
        Success message with deleted file count
        
    Raises:
        HTTPException: If job not found or user not authorized
    """
    try:
        logger.info(f"Delete request for job: {job_id} by user: {current_user.user_id}")
        
        # Get job from database
        job = await db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # ✅ Authorization: Students can only delete their own jobs
        if current_user.role == "student" and job.get("student_id") != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this job")
        
        # ✅ Delete physical files if they exist
        files_to_delete = [
            job.get("original_image_path"),
            job.get("preprocessed_image_path"),
            job.get("report_path")
        ]
        
        deleted_files = []
        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(os.path.basename(file_path))
                    logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete file {file_path}: {str(e)}")
        
        # ✅ Delete job from database
        deleted = await db.delete_job(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found in database")
        
        logger.info(f"Job {job_id} deleted successfully. Removed {len(deleted_files)} file(s)")
        
        return build_response(
            status="success",
            message=f"Job deleted successfully. Removed {len(deleted_files)} file(s)",
            data={
                "job_id": job_id,
                "deleted_files": deleted_files,
                "deleted_count": len(deleted_files)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
