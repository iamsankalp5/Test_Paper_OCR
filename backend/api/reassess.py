"""
Re-assessment endpoint - Re-grade answers with AI.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.services.reference_service import ReferenceService
from app.core.assessment_engine import AssessmentEngine
from app.core.utils import build_response, calculate_percentage, get_grade_from_percentage
from app.models.enums import WorkflowState
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

class ReassessRequest(BaseModel):
    job_id: str
    reference_id: Optional[str] = None  

@router.post("/")
async def reassess_answers(
    request: ReassessRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Re-assess answers using AI with or without reference answers.
    
    If reference_id is provided, uses reference answers for grading.
    If not provided, AI grades based on general knowledge.
    
    Args:
        request: ReassessRequest with job_id and optional reference_id
        
    Returns:
        Updated assessment results
    """
    try:
        logger.info(f"Re-assessment requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Validate that job has parsed answers
        if not job.get('parsed_answers'):
            raise HTTPException(
                status_code=400,
                detail="Job has no parsed answers to re-assess"
            )
        
        answer_key = None
        if request.reference_id:
            logger.info(f"Using reference answers: {request.reference_id}")
            ref_service = ReferenceService(db)
            reference = await ref_service.get_reference(request.reference_id)
            
            if reference and reference.get('reference_answers'):
                answer_key = {
                    ans['question_number']: ans['answer_text']
                    for ans in reference['reference_answers']
                }
                logger.info(f"Found {len(answer_key)} reference answers")
        else:
            logger.info("Re-assessing without reference answers (AI-based grading)")
        
        # Update state to re-assessing
        await db.update_job(request.job_id, {
            "state": WorkflowState.ASSESSING.value,
            "current_step": "reassessing",
            "progress_percentage": 65
        })
        
        assessor = AssessmentEngine()
        assessed_answers = await assessor.assess_answers(
            job['parsed_answers'],
            answer_key  
        )
        
        # Calculate totals
        total_marks_obtained = sum(a['marks_obtained'] for a in assessed_answers)
        total_marks = sum(a['max_marks'] for a in assessed_answers)
        percentage = calculate_percentage(total_marks_obtained, total_marks)
        grade = get_grade_from_percentage(percentage)
        
        # Update job with new assessment
        await db.update_job(request.job_id, {
            "state": WorkflowState.ASSESSED.value,
            "current_step": "assessed",
            "progress_percentage": 75,
            "assessed_answers": assessed_answers,
            "total_marks_obtained": total_marks_obtained,
            "percentage": percentage,
            "grade": grade,
            "reassessed": True 
        })
        
        logger.info(f"Re-assessment completed. Score: {percentage}% | Grade: {grade}")
        
        return build_response(
            status="success",
            message="Re-assessment completed successfully",
            data={
                "assessed_answers": assessed_answers,
                "total_marks_obtained": round(total_marks_obtained, 2),
                "total_marks": total_marks,
                "percentage": percentage,
                "grade": grade
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Re-assessment failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Re-assessment failed: {str(e)}")
