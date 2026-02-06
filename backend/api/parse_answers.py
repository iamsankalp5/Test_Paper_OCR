"""
Answer parsing endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.answer_parser import AnswerParser
from app.models.schemas import ParseAnswersRequest
from app.models.enums import WorkflowState
from app.core.utils import build_response
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/")
async def parse_answers(
    request: ParseAnswersRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Parse OCR text to extract question-answer pairs.
    
    Args:
        request: Parse request with job_id
        
    Returns:
        Parsed answers list
        
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/parse/" \
          -H "Content-Type: application/json" \
          -d '{"job_id": "job_20251022_abc123"}'
        ```
    """
    try:
        logger.info(f"Answer parsing requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Validate state
        if job['state'] != WorkflowState.OCR_EXTRACTED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Job must have OCR extracted. Current state: {job['state']}"
            )
        
        # Update state to parsing
        await db.update_job(request.job_id, {
            "state": WorkflowState.PARSING.value,
            "current_step": "parsing",
            "progress_percentage": 50
        })
        
        # Parse answers
        parser = AnswerParser()
        answers = parser.parse(job['extracted_text'], job['total_marks'])
        
        # Update job with results
        await db.update_job(request.job_id, {
            "state": WorkflowState.PARSED.value,
            "current_step": "parsed",
            "progress_percentage": 55,
            "answers": answers
        })
        
        logger.info(f"Answer parsing completed for job: {request.job_id}")
        
        response_data = {
            "job_id": request.job_id,
            "answers": answers,
            "total_questions": len(answers),
            "state": WorkflowState.PARSED.value
        }
        
        return build_response(
            status="success",
            message="Answer parsing completed successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer parsing failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        return build_response(
            status="error",
            message=f"Answer parsing failed: {str(e)}",
            data=None
        )