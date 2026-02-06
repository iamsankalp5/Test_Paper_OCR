"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.enums import WorkflowState, QuestionType, Grade, Subject

# ============================================================================
# Base Response Schema
# ============================================================================

class BaseResponse(BaseModel):
    """Standard API response format."""
    status: str = Field(..., description="Status: success or error")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="Response data")
    trace: Optional[str] = Field(None, description="Error trace location")

# ============================================================================
# Image Upload Schemas
# ============================================================================

class ImageUploadRequest(BaseModel):
    """Request schema for image upload metadata."""
    student_name: str = Field(..., min_length=1, max_length=200)
    student_id: str = Field(..., min_length=1, max_length=100)
    exam_name: str = Field(..., min_length=1, max_length=200)
    subject: Subject
    total_marks: int = Field(..., gt=0, le=1000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ImageUploadResponse(BaseModel):
    """Response schema for image upload."""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str
    file_size: int
    upload_timestamp: datetime
    state: WorkflowState

# ============================================================================
# Preprocessing Schemas
# ============================================================================

class PreprocessingRequest(BaseModel):
    """Request schema for preprocessing parameters."""
    job_id: str = Field(..., description="Job identifier from upload")

class PreprocessingResponse(BaseModel):
    """Response schema for preprocessing."""
    job_id: str
    preprocessed_image_path: str
    preprocessing_details: Dict[str, Any]
    state: WorkflowState

# ============================================================================
# OCR Extraction Schemas
# ============================================================================

class OCRRequest(BaseModel):
    """Request schema for OCR extraction."""
    job_id: str = Field(..., description="Job identifier")
    use_easyocr: bool = Field(default=False, description="Use EasyOCR instead of Tesseract")
    use_trocr: bool = Field(default=False, description="Use TrOCR for handwritten text recognition")

class OCRResponse(BaseModel):
    """Response schema for OCR extraction."""
    job_id: str
    extracted_text: str
    confidence: float = Field(..., ge=0, le=100)
    ocr_details: Dict[str, Any]
    state: WorkflowState

# ============================================================================
# Answer Parsing Schemas
# ============================================================================

class ParsedAnswer(BaseModel):
    """Schema for a single parsed answer."""
    question_number: int
    question_text: str
    question_type: QuestionType
    answer_text: str
    max_marks: float

class ParseAnswersRequest(BaseModel):
    """Request schema for parsing answers."""
    job_id: str = Field(..., description="Job identifier")

class ParseAnswersResponse(BaseModel):
    """Response schema for parsed answers."""
    job_id: str
    answers: List[ParsedAnswer]
    total_questions: int
    state: WorkflowState

# ============================================================================
# AI Assessment Schemas
# ============================================================================

class AssessedAnswer(BaseModel):
    """Schema for a single assessed answer."""
    question_number: int
    question_text: str
    student_answer: str
    marks_obtained: float
    max_marks: float
    is_correct: bool
    explanation: str
    suggestions: List[str]

class AssessmentRequest(BaseModel):
    """Request schema for AI assessment."""
    job_id: str = Field(..., description="Job identifier")
    answer_key: Optional[Dict[int, str]] = Field(
        None, description="Optional answer key for objective questions"
    )

class AssessmentResponse(BaseModel):
    """Response schema for AI assessment."""
    job_id: str
    assessed_answers: List[AssessedAnswer]
    total_marks_obtained: float
    total_marks: float
    percentage: float
    state: WorkflowState

# ============================================================================
# Feedback Generation Schemas
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request schema for feedback generation."""
    job_id: str = Field(..., description="Job identifier")

class FeedbackResponse(BaseModel):
    """Response schema for feedback generation."""
    job_id: str
    overall_feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    recommendations: List[str]
    grade: Grade
    state: WorkflowState

# ============================================================================
# Review Schemas
# ============================================================================

class ReviewUpdate(BaseModel):
    """Schema for review updates."""
    question_number: int
    marks_obtained: Optional[float] = None
    explanation: Optional[str] = None
    reviewer_notes: Optional[str] = None

class ReviewRequest(BaseModel):
    """Request schema for review."""
    job_id: str = Field(..., description="Job identifier")
    updates: List[ReviewUpdate]
    reviewer_name: str
    reviewer_comments: Optional[str] = None

class ReviewResponse(BaseModel):
    """Response schema for review."""
    job_id: str
    updates_applied: int
    state: WorkflowState

# ============================================================================
# Report Generation Schemas
# ============================================================================

class ReportRequest(BaseModel):
    """Request schema for report generation."""
    job_id: str = Field(..., description="Job identifier")
    format: str = Field(default="pdf", pattern="^(pdf|json)$")
    include_original_image: bool = Field(default=False)

class ReportResponse(BaseModel):
    """Response schema for report."""
    job_id: str
    report_path: str
    report_url: Optional[str] = None
    state: WorkflowState

# ============================================================================
# Job Status Schema
# ============================================================================

class JobStatusResponse(BaseModel):
    """Response schema for job status."""
    job_id: str
    state: WorkflowState
    current_step: str
    progress_percentage: int
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

# ============================================================================
# Reference Document Schemas (Teacher Side)
# ============================================================================

class ReferenceUploadRequest(BaseModel):
    """Request schema for reference document upload metadata."""
    teacher_name: str = Field(..., min_length=1, max_length=200)
    teacher_id: str = Field(..., min_length=1, max_length=100)
    exam_name: str = Field(..., min_length=1, max_length=200)
    subject: Subject
    total_marks: int = Field(..., gt=0, le=1000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReferenceUploadResponse(BaseModel):
    """Response schema for reference upload."""
    reference_id: str = Field(..., description="Unique reference identifier")
    filename: str
    file_size: int
    upload_timestamp: datetime
    is_active: bool


class ReferenceProcessRequest(BaseModel):
    """Request to process reference document."""
    reference_id: str = Field(..., description="Reference identifier")


class ReferenceListResponse(BaseModel):
    """Response schema for listing references."""
    references: List[Dict[str, Any]]
    total: int

# ============================================================================
# Modified Image Upload Schema (Student Side)
# ============================================================================

class ImageUploadRequest(BaseModel):
    """Request schema for image upload metadata."""
    student_name: str = Field(..., min_length=1, max_length=200)
    student_id: str = Field(..., min_length=1, max_length=100)
    exam_name: str = Field(..., min_length=1, max_length=200)
    subject: Subject
    total_marks: int = Field(..., gt=0, le=1000)
    
    # ADD THIS NEW FIELD
    reference_id: Optional[str] = Field(None, description="Reference document to use for grading")
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)