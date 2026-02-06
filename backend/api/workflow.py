"""
Autonomous Workflow API - Multi-Agent Collaboration Endpoint
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from app.core.workflow_manager import WorkflowManager
from app.core.utils import build_response
from app.config.logging_config import get_logger
from app.core.auth import get_current_student
from app.models.user import UserInDB
from app.dependencies import get_storage_service, get_db_service
from app.services.storage_service import StorageService
from app.services.database_service import DatabaseService

logger = get_logger(__name__)
router = APIRouter()

@router.post("/autonomous")
async def execute_autonomous_workflow(
    file: UploadFile = File(..., description="Student test paper (image or PDF)"),
    student_name: str = Form(..., description="Student name"),
    student_id: str = Form(..., description="Student ID"),
    reference_id: Optional[str] = Form(None, description="Reference answer key ID"),
    exam_name: Optional[str] = Form(None, description="Exam name"),
    subject: Optional[str] = Form(None, description="Subject"),
    total_marks: int = Form(100, description="Total marks"),
    current_student: UserInDB = Depends(get_current_student),  # ADD THIS
    storage: StorageService = Depends(get_storage_service),
    db: DatabaseService = Depends(get_db_service)
):
    """
    **FULLY AUTONOMOUS MULTI-AGENT WORKFLOW**
    
    Upload a test paper and let specialized AI agents collaborate to:
    
    1. **Vision Agent**: Extract text using OCR (Tesseract)
    2. **Parser Agent**: Structure answers using NLP
    3. **Assessment Agent**: Grade answers using Gemini AI
    4. **Feedback Agent**: Generate personalized feedback using Gemini AI
    5. **Report Agent**: Create professional PDF report
    
    **Zero human intervention required!** All agents work together autonomously.
    
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/workflow/autonomous" \\
          -F "file=@student_test.pdf" \\
          -F "student_name=John Doe" \\
          -F "student_id=STU001" \\
          -F "reference_id=ref_xxx" \\
          -F "total_marks=100"
        ```
    
    Returns:
        Complete workflow result with:
        - Final score and grade
        - All agent execution logs
        - Download link for PDF report
    """

    """Execute autonomous workflow (student only)."""
    try:
        # Override student_name with authenticated user
        student_name = current_student.full_name
        student_id = current_student.user_id
        logger.info(f"Autonomous workflow initiated for {student_name}")
        
        # Initialize workflow manager
        workflow_manager = WorkflowManager()
        
        # Execute autonomous pipeline
        result = await workflow_manager.execute_autonomous_pipeline(
            file=file,
            student_name=student_name,
            student_id=student_id,
            reference_id=reference_id,
            exam_name=exam_name,
            subject=subject,
            total_marks=total_marks
        )
        
        logger.info(f"Autonomous workflow completed: {result['job_id']}")
        
        return build_response(
            status="success",
            message=f"Agentic AI workflow completed! Score: {result['final_score']} | Grade: {result['grade']}",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Autonomous workflow failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )