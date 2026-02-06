"""
Database document models for MongoDB collections.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import WorkflowState, QuestionType, Grade, Subject

class ReferenceDocument(BaseModel):
    """MongoDB document model for teacher reference answers."""
    reference_id: str = Field(..., description="Unique reference identifier")
    teacher_name: str
    teacher_id: str
    exam_name: str
    subject: Subject
    total_marks: int
    
    # Reference file paths
    original_reference_path: str
    processed_reference_path: Optional[str] = None
    
    # Extracted reference data
    reference_text: Optional[str] = None
    reference_answers: Optional[List[Dict[str, Any]]] = None  # Parsed Q&A
    
    # Status
    is_active: bool = True
    ocr_completed: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "reference_id": "ref_abc123",
                "teacher_name": "Prof. Smith",
                "teacher_id": "TCH001",
                "exam_name": "Mid Term Math Test",
                "subject": "Mathematics",
                "total_marks": 100
            }
        }


class JobDocument(BaseModel):
    """MongoDB document model for job tracking."""
    job_id: str = Field(..., description="Unique job identifier")
    reference_id: Optional[str] = None  # Link to teacher's reference document
    student_name: str
    student_id: str
    exam_name: str
    subject: Subject
    total_marks: int

    # File paths
    original_image_path: str
    processed_image_path: Optional[str] = None
    report_path: Optional[str] = None

    # Workflow state
    state: WorkflowState = WorkflowState.UPLOADED
    current_step: str = "uploaded"
    progress_percentage: int = 0

    # OCR data
    extracted_text: Optional[str] = None
    ocr_confidence: Optional[float] = None

    # Parsed answers
    answers: Optional[List[Dict[str, Any]]] = None

    # Assessment results
    assessed_answers: Optional[List[Dict[str, Any]]] = None
    total_marks_obtained: Optional[float] = None
    percentage: Optional[float] = None

    # Feedback
    overall_feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    grade: Optional[Grade] = None

    # Review data
    reviewed: bool = False
    reviewer_name: Optional[str] = None
    reviewer_comments: Optional[str] = None
    review_updates: Optional[List[Dict[str, Any]]] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.timezone.utc)
    updated_at: datetime = Field(default_factory=datetime.timezone.utc)

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123",
                "student_name": "John Doe",
                "student_id": "STU001",
                "exam_name": "Mid Term Math Test",
                "subject": "Mathematics",
                "total_marks": 100,
                "original_image_path": "uploads/job_abc123_original.jpg",
                "state": "uploaded",
                "current_step": "uploaded",
                "progress_percentage": 10
            }
        }    