"""
Feedback generation endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.feedback_generator import FeedbackGenerator
from app.models.schemas import FeedbackRequest
from app.models.enums import WorkflowState
from app.core.utils import build_response
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/")
async def generate_feedback(
    request: FeedbackRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Generate personalized feedback for student.
    
    Args:
        request: Feedback request with job_id
        
    Returns:
        Personalized feedback and recommendations
        
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/feedback/" \
          -H "Content-Type: application/json" \
          -d '{"job_id": "job_20251022_abc123"}'
        ```
    """
    try:
        logger.info(f"Feedback generation requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Validate state
        if job['state'] != WorkflowState.ASSESSED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Job must be assessed first. Current state: {job['state']}"
            )
        
        # Update state to generating feedback
        await db.update_job(request.job_id, {
            "state": WorkflowState.GENERATING_FEEDBACK.value,
            "current_step": "generating_feedback",
            "progress_percentage": 80
        })
        
        # Generate feedback
        feedback_gen = FeedbackGenerator()
        feedback = await feedback_gen.generate_feedback(
            job['student_name'],
            job['subject'],
            job['assessed_answers'],
            job['percentage']
        )
        
        # Update job with results
        await db.update_job(request.job_id, {
            "state": WorkflowState.FEEDBACK_GENERATED.value,
            "current_step": "feedback_generated",
            "progress_percentage": 85,
            "overall_feedback": feedback['overall_feedback'],
            "strengths": feedback['strengths'],
            "areas_for_improvement": feedback['areas_for_improvement'],
            "recommendations": feedback['recommendations'],
            "grade": feedback['grade']
        })
        
        logger.info(f"Feedback generation completed for job: {request.job_id}")
        
        response_data = {
            "job_id": request.job_id,
            "overall_feedback": feedback['overall_feedback'],
            "strengths": feedback['strengths'],
            "areas_for_improvement": feedback['areas_for_improvement'],
            "recommendations": feedback['recommendations'],
            "grade": feedback['grade'],
            "state": WorkflowState.FEEDBACK_GENERATED.value
        }
        
        return build_response(
            status="success",
            message="Feedback generated successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback generation failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        return build_response(
            status="error",
            message=f"Feedback generation failed: {str(e)}",
            data=None
        )