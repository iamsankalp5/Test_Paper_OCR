"""
AI assessment endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.assessment_engine import AssessmentEngine
from app.models.schemas import AssessmentRequest
from app.models.enums import WorkflowState
from app.core.utils import build_response, calculate_percentage
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/")
async def assess_answers(
    request: AssessmentRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Perform AI-based assessment of parsed answers.
    
    Args:
        request: Assessment request with job_id and optional answer_key
        
    Returns:
        Assessment results with marks and feedback
        
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/assess/" \
          -H "Content-Type: application/json" \
          -d '{
            "job_id": "job_20251022_abc123",
            "answer_key": {"1": "42", "2": "Paris"}
          }'
        ```
    """
    try:
        logger.info(f"AI assessment requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Validate state
        if job['state'] != WorkflowState.PARSED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Job must have answers parsed. Current state: {job['state']}"
            )
        
        # ADD: Fetch reference answers if reference_id exists
        reference_answers_map = None
        if job.get('reference_id'):
            from app.services.reference_service import ReferenceService
            ref_service = ReferenceService(db)
            reference = await ref_service.get_reference(job['reference_id'])
            
            if reference and reference.get('reference_answers'):
                # Convert reference answers to a map for easy lookup
                reference_answers_map = {
                    ans['question_number']: ans['answer_text']
                    for ans in reference['reference_answers']
                }
                logger.info(f"Using reference answers from: {job['reference_id']}")
        
        # If manual answer_key provided, it takes precedence
        answer_key = request.answer_key or reference_answers_map
        
        # Update state to assessing
        await db.update_job(request.job_id, {
            "state": WorkflowState.ASSESSING.value,
            "current_step": "assessing",
            "progress_percentage": 65
        })
        
        # Perform assessment
        assessor = AssessmentEngine()
        assessed_answers = await assessor.assess_answers(
            job['answers'],
            answer_key # This now includes reference answers
        )
        
        # Calculate totals
        total_marks_obtained = sum(a['marks_obtained'] for a in assessed_answers)
        total_marks = sum(a['max_marks'] for a in assessed_answers)
        percentage = calculate_percentage(total_marks_obtained, total_marks)
        
        # Update job with results
        await db.update_job(request.job_id, {
            "state": WorkflowState.ASSESSED.value,
            "current_step": "assessed",
            "progress_percentage": 70,
            "assessed_answers": assessed_answers,
            "total_marks_obtained": total_marks_obtained,
            "percentage": percentage
        })
        
        logger.info(f"AI assessment completed for job: {request.job_id}")
        
        response_data = {
            "job_id": request.job_id,
            "assessed_answers": assessed_answers,
            "total_marks_obtained": round(total_marks_obtained, 2),
            "total_marks": total_marks,
            "percentage": percentage,
            "state": WorkflowState.ASSESSED.value
        }
        
        return build_response(
            status="success",
            message="AI assessment completed successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI assessment failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        return build_response(
            status="error",
            message=f"AI assessment failed: {str(e)}",
            data=None
        )