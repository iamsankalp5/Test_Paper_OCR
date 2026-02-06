"""
Teacher Dashboard API - View student submissions and reports.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.core.auth import get_current_teacher
from app.models.user import UserInDB
from app.services.database_service import DatabaseService
from app.dependencies import get_db
from app.core.utils import build_response
from app.config.logging_config import get_logger
from app.core.utils import get_grade_from_percentage

logger = get_logger(__name__)
router = APIRouter(prefix="/teacher", tags=["Teacher Dashboard"])


@router.get("/my-references")
async def get_my_references(
    current_teacher: UserInDB = Depends(get_current_teacher),
    db: DatabaseService = Depends(get_db)
):
    """
    Get all reference answer keys uploaded by this teacher.
    
    Returns:
        List of teacher's references with submission counts
    """
    try:
        logger.info(f"Fetching references for teacher: {current_teacher.email}")
        
        # Get all references by this teacher
        references = await db.get_references_by_teacher(current_teacher.email)
        
        # Add submission count to each reference
        for ref in references:
            ref['submission_count'] = await db.count_submissions_for_reference(ref['reference_id'])
        
        return build_response(
            status="success",
            message=f"Found {len(references)} reference answer keys",
            data=references
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch references: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions/{reference_id}")
async def get_submissions_for_reference(
    reference_id: str,
    current_teacher: UserInDB = Depends(get_current_teacher),
    db: DatabaseService = Depends(get_db)
):
    """
    Get all student submissions for a specific reference (exam).
    
    Teachers can only view submissions for their own reference keys.
    
    Args:
        reference_id: Reference answer key ID
        
    Returns:
        List of student submissions with scores and status
    """
    try:
        logger.info(f"Fetching submissions for reference: {reference_id}")
        
        # Verify this reference belongs to the teacher
        reference = await db.get_reference_by_id(reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Reference not found")
        
        if reference.get('teacher_email') != current_teacher.email:
            raise HTTPException(
                status_code=403,
                detail="You can only view submissions for your own exams"
            )
        
        # Get all submissions for this reference
        submissions = await db.get_submissions_by_reference(reference_id)
        
        # Format response with essential info
        formatted_submissions = []
        for sub in submissions:
            percentage = sub.get('percentage', 0)
    
            # Calculate grade if missing or N/A
            grade = sub.get('grade', 'N/A')
            if not grade or grade == 'N/A':
                grade = get_grade_from_percentage(percentage)

            formatted_submissions.append({
                "job_id": sub.get('job_id'),
                "student_name": sub.get('student_name'),
                "student_id": sub.get('student_id'),
                "percentage": sub.get('percentage', 0),
                "grade": grade,
                "total_marks_obtained": sub.get('total_marks_obtained', 0),
                "total_marks": sub.get('total_marks', 100),
                "submitted_at": sub.get('created_at'),
                "status": sub.get('state', 'unknown')
            })
        
        return build_response(
            status="success",
            message=f"Found {len(formatted_submissions)} submissions",
            data={
                "reference_id": reference_id,
                "exam_name": reference.get('exam_name'),
                "subject": reference.get('subject'),
                "submissions": formatted_submissions
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch submissions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student-report/{job_id}")
async def get_student_report(
    job_id: str,
    current_teacher: UserInDB = Depends(get_current_teacher),
    db: DatabaseService = Depends(get_db)
):
    """
    Get detailed report for a specific student submission.
    
    Returns complete feedback, assessed answers, and performance details.
    
    Args:
        job_id: Job ID of the student submission
        
    Returns:
        Complete student report with feedback
    """
    try:
        logger.info(f"Fetching report for job: {job_id}")
        
        # Get job details
        job = await db.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Verify this job is for teacher's reference
        reference_id = job.get('reference_id')
        if reference_id:
            reference = await db.get_reference_by_id(reference_id)
            if reference and reference.get('teacher_email') != current_teacher.email:
                raise HTTPException(
                    status_code=403,
                    detail="You can only view reports for your own exams"
                )
            
        # Calculate grade if missing
        from app.core.utils import get_grade_from_percentage
        percentage = job.get('percentage', 0)
        grade = job.get('grade', 'N/A')
        if not grade or grade == 'N/A':
            grade = get_grade_from_percentage(percentage)
        
        # Build comprehensive report
        report = {
            "job_id": job.get('job_id'),
            "student_info": {
                "name": job.get('student_name'),
                "id": job.get('student_id')
            },
            "exam_info": {
                "name": job.get('exam_name'),
                "subject": job.get('subject'),
                "total_marks": job.get('total_marks'),
                "submitted_at": job.get('created_at')
            },
            "performance": {
                "marks_obtained": job.get('total_marks_obtained', 0),
                "percentage": job.get('percentage', 0),
                "grade": grade
            },
            "feedback": job.get('feedback', {}),
            "assessed_answers": job.get('assessed_answers', []),
            "report_url": f"/api/v1/report/download/{job_id}"
        }
        
        return build_response(
            status="success",
            message="Student report retrieved successfully",
            data=report
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class-statistics/{reference_id}")
async def get_class_statistics(
    reference_id: str,
    current_teacher: UserInDB = Depends(get_current_teacher),
    db: DatabaseService = Depends(get_db)
):
    """
    Get statistical overview for all submissions of an exam.
    
    Provides average score, grade distribution, etc.
    
    Args:
        reference_id: Reference answer key ID
        
    Returns:
        Class statistics and analytics
    """
    try:
        logger.info(f"Calculating statistics for reference: {reference_id}")
        
        # Verify ownership
        reference = await db.get_reference_by_id(reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Reference not found")
        
        if reference.get('teacher_email') != current_teacher.email:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all submissions
        submissions = await db.get_submissions_by_reference(reference_id)
        
        if not submissions:
            return build_response(
                status="success",
                message="No submissions yet",
                data={
                    "total_students": 0,
                    "average_score": 0,
                    "grade_distribution": {
                        "A": 0,
                        "B": 0,
                        "C": 0,
                        "D": 0,
                        "F": 0
                    }
                }
            )
        
        # Calculate statistics
        scores = [s.get('percentage', 0) for s in submissions]
        grades = []
        for s in submissions:
            percentage = s.get('percentage', 0)
            grade = s.get('grade', 'N/A')
            
            # Calculate if missing or invalid
            if not grade or grade == 'N/A':
                grade = get_grade_from_percentage(percentage)
            
            grades.append(grade)
        
        # Grade distribution
        grade_dist = {
            "A": grades.count("A"),
            "B": grades.count("B"),
            "C": grades.count("C"),
            "D": grades.count("D"),
            "F": grades.count("F")
        }
        for grade in ['A', 'B', 'C', 'D', 'F']:
            grade_dist[grade] = grades.count(grade)
        
        statistics = {
            "total_students": len(submissions),
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "grade_distribution": grade_dist,
            "pass_rate": round((len([s for s in scores if s >= 60]) / len(scores)) * 100, 2)
        }
        
        return build_response(
            status="success",
            message="Statistics calculated successfully",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))