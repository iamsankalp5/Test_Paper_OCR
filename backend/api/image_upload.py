"""
Image upload endpoint for receiving scanned test papers.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from datetime import datetime
from app.dependencies import get_database, get_storage
from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.models.schemas import ImageUploadResponse
from app.models.enums import WorkflowState, Subject
from app.core.utils import (
    generate_job_id,
    validate_file_extension,
    build_response
)
from app.config.settings import get_settings
from app.config.logging_config import get_logger
from typing import Optional

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=dict)
async def upload_image(
    file: UploadFile = File(..., description="Test paper image file"),
    student_name: str = Form(..., description="Student name"),
    student_id: str = Form(..., description="Student ID"),
    exam_name: str = Form(..., description="Exam name"),
    subject: str = Form(..., description="Subject name"),
    # ADD THIS NEW PARAMETER
    reference_id: Optional[str] = Form(None, description="Reference document ID to use"),

    total_marks: int = Form(..., description="Total marks for the exam"),
    db: DatabaseService = Depends(get_database),
    storage: StorageService = Depends(get_storage),
    settings = Depends(get_settings)
):
    """
    Upload test paper image and create a new assessment job.
    
    Args:
        file: Uploaded image file
        student_name: Name of the student
        student_id: Student identifier
        exam_name: Name of the exam
        subject: Subject of the exam
        total_marks: Total marks for the exam
        
    Returns:
        Job information with job_id
        
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/upload/" \
          -F "file=@test_paper.jpg" \
          -F "student_name=John Doe" \
          -F "student_id=STU001" \
          -F "exam_name=Mid Term Math Test" \
          -F "subject=Mathematics" \
          -F "total_marks=100"
        ```
    """
    try:
        logger.info(f"Image upload requested for student: {student_name}")

        # ADD: Validate reference if provided
        if reference_id:
            from app.services.reference_service import ReferenceService
            ref_service = ReferenceService(db)
            reference = await ref_service.get_reference(reference_id)
            
            if not reference:
                raise HTTPException(
                    status_code=404,
                    detail=f"Reference document not found: {reference_id}"
                )
            
            if not reference.get('ocr_completed'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Reference document must be processed first. Call /reference/process/{reference_id}"
                )
            
            logger.info(f"Using reference document: {reference_id}")
        
        # Validate file extension
        if not validate_file_extension(file.filename, settings.allowed_extensions_list):
            logger.warning(f"Invalid file extension: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {settings.allowed_extensions}"
            )
        
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.max_file_size:
            logger.warning(f"File too large: {file_size} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Generate job ID
        job_id = generate_job_id()
        logger.info(f"Generated job ID: {job_id}")
        
        # Save uploaded file
        original_path, saved_size = await storage.save_uploaded_file(
            file, job_id, "original"
        )
        
        # Prepare job document
        job_data = {
            "job_id": job_id,
            "student_name": student_name,
            "student_id": student_id,
            "exam_name": exam_name,
            "subject": subject,
            "total_marks": total_marks,
            "reference_id": reference_id,
            "original_image_path": original_path,
            "processed_image_path": storage.get_file_path(job_id, "processed", ".jpg"),
            "report_path": storage.get_file_path(job_id, "report", ".pdf"),
            "state": WorkflowState.UPLOADED.value,
            "current_step": "uploaded",
            "progress_percentage": 10,
            "metadata": {
                "original_filename": file.filename,
                "file_size": saved_size,
                "content_type": file.content_type
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save to database
        await db.create_job(job_data)
        logger.info(f"Job created successfully: {job_id}")
        
        # Build response
        response_data = ImageUploadResponse(
            job_id=job_id,
            filename=file.filename,
            file_size=saved_size,
            upload_timestamp=datetime.utcnow(),
            state=WorkflowState.UPLOADED
        )
        
        return build_response(
            status="success",
            message=f"Image uploaded successfully. Job ID: {job_id}",
            data=response_data.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Image upload failed: {str(e)}",
            data=None
        )


@router.get("/{job_id}/status")
async def get_upload_status(
    job_id: str,
    db: DatabaseService = Depends(get_database)
):
    """
    Get status of an uploaded job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Current job status
        
    Example:
        ```
        curl "http://localhost:8000/api/v1/upload/job_20251022_abc123/status"
        ```
    """
    try:
        logger.debug(f"Status check requested for job: {job_id}")
        
        job = await db.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        status_data = {
            "job_id": job.get("job_id"),
            "state": job.get("state"),
            "current_step": job.get(
                "current_step", "completed" if job.get("state") == "completed" else None
            ),
            "progress_percentage": job.get("progress_percentage"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
            "error_message": job.get("error_message"),
        }

        # Return grading/results if present
        for field in [
            "student_name",
            "exam_name",
            "subject",
            "total_marks",
            "marks_obtained",
            "grade",
            "percentage",
            "feedback",
            "insights",
            "answers",
            "reference_id",
            "report_path"
        ]:
            if field in job:
                status_data[field] = job[field]

        # Extra fields for AI/agent workflow results
        if "assessed_answers" in job:
            status_data["answers"] = job["assessed_answers"]
        if "total_marks_obtained" in job:
            status_data["marks_obtained"] = job["total_marks_obtained"]
        if "percentage" in job:
            status_data["percentage"] = job["percentage"]
        if "grade" in job:
            status_data["grade"] = job["grade"]
        if "feedback" in job and isinstance(job["feedback"], dict):
            # Unpack feedback dict
            status_data["insights"] = {
                "feedback": job["feedback"].get("overall_feedback", ""),
                "strengths": job["feedback"].get("strengths", []),
                "improvements": job["feedback"].get("areas_for_improvement", []),
                "recommendations": job["feedback"].get("recommendations", []),
            }
        
        return build_response(
            status="success",
            message="Job status and results retrieved",
            data=status_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status retrieval failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Status retrieval failed: {str(e)}",
            data=None
        )