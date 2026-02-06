"""
Report generation and delivery endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.report_generator import ReportGenerator
from app.models.schemas import ReportRequest
from app.models.enums import WorkflowState
from app.core.utils import build_response
from app.config.logging_config import get_logger
import os

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Generate final assessment report.
    """
    try:
        logger.info(f"Report generation requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Validate state
        valid_states = [
            WorkflowState.FEEDBACK_GENERATED.value,
            WorkflowState.REVIEWED.value,
            WorkflowState.COMPLETED.value
        ]
        if job['state'] not in valid_states:
            raise HTTPException(
                status_code=400,
                detail=f"Job must have feedback generated. Current state: {job['state']}"
            )
        
        # Ensure report directory exists
        report_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # Ensure report_path is present and valid
        if not job.get("report_path"):
            job["report_path"] = os.path.join(report_dir, f"{request.job_id}.pdf")
        
        # Update state to generating report
        await db.update_job(request.job_id, {
            "state": WorkflowState.REPORT_GENERATING.value,
            "current_step": "report_generating",
            "progress_percentage": 95,
            "report_path": job["report_path"]
        })
        
        # Generate report
        report_gen = ReportGenerator()
        
        if request.format == "pdf":
            report_path = report_gen.generate_pdf_report(job, job["report_path"])
        elif request.format == "json":
            json_path = job['report_path'].replace('.pdf', '.json')
            report_path = report_gen.generate_json_report(job, json_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        # Update job with completion
        await db.update_job(request.job_id, {
            "state": WorkflowState.COMPLETED.value,
            "current_step": "completed",
            "progress_percentage": 100,
            "report_path": report_path
        })
        
        logger.info(f"Report generated successfully for job: {request.job_id}")
        
        response_data = {
            "job_id": request.job_id,
            "report_path": report_path,
            "report_url": f"/api/v1/report/download/{request.job_id}",
            "format": request.format,
            "state": WorkflowState.COMPLETED.value
        }
        
        return build_response(
            status="success",
            message="Report generated successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        return build_response(
            status="error",
            message=f"Report generation failed: {str(e)}",
            data=None
        )


@router.get("/download/{job_id}")
async def download_report(
    job_id: str,
    db: DatabaseService = Depends(get_database)
):
    """
    Download generated report.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Report file for download
        
    Example:
        ```
        curl "http://localhost:8000/api/v1/report/download/job_20251022_abc123" \
          --output report.pdf
        ```
    """
    try:
        logger.info(f"Report download requested for job: {job_id}")
        
        # Get job from database
        job = await db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        # Check if report exists
        report_path = job.get('report_path')
        if not report_path or not os.path.exists(report_path):
            raise HTTPException(status_code=404, detail="Report not found. Please generate it first.")
        
        # Determine filename
        filename = f"{job_id}_report{os.path.splitext(report_path)[1]}"
        
        return FileResponse(
            path=report_path,
            filename=filename,
            media_type='application/pdf' if report_path.endswith('.pdf') else 'application/json'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report download failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report download failed: {str(e)}")


@router.get("/{job_id}")
async def get_report_status(
    job_id: str,
    db: DatabaseService = Depends(get_database)
):
    """
    Get report generation status.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Report status information
    """
    try:
        job = await db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        report_ready = job['state'] == WorkflowState.COMPLETED.value
        
        status_data = {
            "job_id": job_id,
            "report_ready": report_ready,
            "report_path": job.get('report_path'),
            "state": job['state'],
            "progress_percentage": job['progress_percentage']
        }
        
        return build_response(
            status="success",
            message="Report status retrieved",
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