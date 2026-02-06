"""
Teacher review and correction endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.reviewer import Reviewer
from app.core.utils import build_response, get_grade_from_percentage
from app.models.schemas import ReviewRequest
from app.models.enums import WorkflowState
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/")
async def review_assessment(
    request: ReviewRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Apply teacher review updates to assessment.
    
    Args:
        request: Review request with job_id, updates, and reviewer info
        
    Returns:
        Updated assessment results
        
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/review/" \
          -H "Content-Type: application/json" \
          -d '{
            "job_id": "job_20251022_abc123",
            "updates": [
              {"question_number": 1, "marks_obtained": 8.5, "explanation": "Corrected grading"}
            ],
            "reviewer_name": "Prof. Smith",
            "reviewer_comments": "Overall good performance"
          }'
        ```
    """
    try:
        logger.info(f"Review requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Validate state
        if job['state'] not in [WorkflowState.ASSESSED.value, WorkflowState.FEEDBACK_GENERATED.value]:
            raise HTTPException(
                status_code=400,
                detail=f"Job must be assessed first. Current state: {job['state']}"
            )
        
        # Update state to under review
        await db.update_job(request.job_id, {
            "state": WorkflowState.UNDER_REVIEW.value,
            "current_step": "under_review",
            "progress_percentage": 90
        })
        
        # Apply review updates
        reviewer = Reviewer()
        updated_answers, updates_applied = reviewer.apply_review_updates(
            job['assessed_answers'],
            [update.dict() for update in request.updates],
            request.reviewer_name
        )
        
        # Recalculate totals
        totals = reviewer.recalculate_totals(updated_answers)
        new_grade = get_grade_from_percentage(totals['percentage'])
        
        # Update job with review results
        await db.update_job(request.job_id, {
            "state": WorkflowState.REVIEWED.value,
            "current_step": "reviewed",
            "progress_percentage": 92,
            "assessed_answers": updated_answers,
            "total_marks_obtained": totals['total_marks_obtained'],
            "percentage": totals['percentage'],
            "grade": new_grade,
            "reviewed": True,
            "reviewer_name": request.reviewer_name,
            "reviewer_comments": request.reviewer_comments,
            "review_updates": [update.dict() for update in request.updates]
        })
        
        logger.info(f"Review completed for job: {request.job_id}. {updates_applied} updates applied.")
        
        response_data = {
            "job_id": request.job_id,
            "updates_applied": updates_applied,
            "new_total_marks": totals['total_marks_obtained'],
            "new_percentage": totals['percentage'],
            "new_grade": new_grade,
            "state": WorkflowState.REVIEWED.value
        }
        
        return build_response(
            status="success",
            message=f"Review completed. {updates_applied} updates applied.",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        return build_response(
            status="error",
            message=f"Review failed: {str(e)}",
            data=None
        )