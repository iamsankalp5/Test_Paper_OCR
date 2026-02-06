"""
History API - View past uploads and results.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.auth import get_current_user
from app.models.user import UserInDB
from app.core.utils import build_response
from app.config.logging_config import get_logger
from datetime import datetime, timezone, timedelta  # ✅ Added timedelta



logger = get_logger(__name__)
router = APIRouter()



@router.get("/")
async def get_user_history(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: UserInDB = Depends(get_current_user),
    db: DatabaseService = Depends(get_database)
):
    try:
        logger.info(f"Fetching history for user: {current_user.user_id} (role: {current_user.role})")
        
        # Build query based on role
        query = {}
        
        if current_user.role == "student":
            query["student_id"] = current_user.user_id
        
        if status:
            query["state"] = status
        
        jobs = await db.get_jobs_by_query(query, limit=limit, sort_by="created_at", sort_order=-1)
        
        IST = timezone(timedelta(hours=5, minutes=30))
        
        # Format response
        history_items = []
        for job in jobs:
            created_at = job.get("created_at")
            if isinstance(created_at, datetime):
                # Ensure always UTC and ISO with 'Z'
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                else:
                    created_at = created_at.astimezone(timezone.utc)
                created_at = created_at.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            
            updated_at = job.get("updated_at")
            if isinstance(updated_at, datetime):
                # If datetime is naive (no timezone), assume it's IST
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=IST)
                
                # Convert to ISO string with timezone
                updated_at = updated_at.isoformat()
            
            history_items.append({
                "job_id": job["job_id"],
                "student_name": job.get("student_name", "Unknown"),
                "student_id": job.get("student_id", "Unknown"),
                "exam_name": job.get("exam_name", "Unknown Exam"),
                "subject": job.get("subject", "Unknown Subject"),
                "percentage": job.get("percentage", 0),
                "grade": job.get("grade", "N/A"),
                "state": job.get("state", "unknown"),
                "created_at": created_at,  
                "updated_at": updated_at,  
                "total_marks": job.get("total_marks", 0),
                "total_marks_obtained": job.get("total_marks_obtained", 0)
            })
        
        logger.info(f"Found {len(history_items)} history items")


        return build_response(
            status="success",
            message=f"Found {len(history_items)} upload(s)",
            data={
                "history": history_items,
                "total": len(history_items)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")
