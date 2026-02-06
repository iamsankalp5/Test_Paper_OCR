"""
Teacher reference document upload and management endpoint.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from datetime import datetime, timezone
from typing import Optional

from app.dependencies import get_database, get_storage
from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.services.reference_service import ReferenceService
from app.core.image_preprocessor import ImagePreprocessor
from app.core.ocr_engine import OCREngine
from app.core.answer_parser import AnswerParser
from app.models.schemas import ReferenceUploadResponse, ReferenceListResponse
from app.models.enums import Subject
from app.core.utils import (
    generate_job_id,
    validate_file_extension,
    build_response
)
from app.config.settings import get_settings
from app.config.logging_config import get_logger
from app.core.auth import get_current_teacher
from app.models.user import UserInDB

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_reference(
    file: UploadFile = File(..., description="Reference answer key document"),
    exam_name: str = Form(..., description="Exam name"),
    subject: str = Form(..., description="Subject name"),
    total_marks: int = Form(..., description="Total marks"),
    current_teacher: UserInDB = Depends(get_current_teacher),
    db: DatabaseService = Depends(get_database),
    storage: StorageService = Depends(get_storage),
    settings = Depends(get_settings)
):
    """
    Upload teacher's reference answer document.
    
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/reference/upload" \
          -F "file=@answer_key.jpg" \
          -F "teacher_name=Prof. Smith" \
          -F "teacher_id=TCH001" \
          -F "exam_name=Mid Term Math Test" \
          -F "subject=Mathematics" \
          -F "total_marks=100"
        ```
    """
    
    """Upload reference (teacher only)."""
    # Use current_teacher.email instead of teacher_name from form
    teacher_name = current_teacher.full_name

    try:
        logger.info(f"Reference upload requested by teacher: {current_teacher.full_name} ({current_teacher.email}")
        
        # Validate file
        if not validate_file_extension(file.filename, settings.allowed_extensions_list):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {settings.allowed_extensions}"
            )
        
        # Generate reference ID
        reference_id = f"ref_{generate_job_id().split('_', 1)[1]}"
        logger.info(f"Generated reference ID: {reference_id}")
        
        # Save uploaded file
        original_path, saved_size = await storage.save_uploaded_file(
            file, reference_id, "reference_original"
        )
        
        # Prepare reference document
        reference_data = {
            "reference_id": reference_id,
            "teacher_name": current_teacher.full_name,     # From authenticated user
            "teacher_email": current_teacher.email,     # NEW: Add teacher email
            "teacher_id": current_teacher.user_id,      # Changed: Use authenticated teacher ID
            "exam_name": exam_name,
            "subject": subject,
            "total_marks": total_marks,
            "original_reference_path": original_path,
            "processed_reference_path": storage.get_file_path(
                reference_id, "reference_processed", ".jpg"
            ),
            "is_active": True,
            "ocr_completed": False,
            "metadata": {
                "original_filename": file.filename,
                "file_size": saved_size,
                "content_type": file.content_type
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Save to database
        ref_service = ReferenceService(db)
        await ref_service.create_reference(reference_data)
        
        logger.info(f"Reference created successfully: {reference_id}")
        
        response_data = ReferenceUploadResponse(
            reference_id=reference_id,
            filename=file.filename,
            file_size=saved_size,
            upload_timestamp=datetime.now(timezone.utc),
            is_active=True
        )
        
        return build_response(
            status="success",
            message=f"Reference uploaded successfully. Reference ID: {reference_id}",
            data=response_data.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reference upload failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Reference upload failed: {str(e)}",
            data=None
        )


@router.post("/process/{reference_id}")
async def process_reference(
    reference_id: str,
    db: DatabaseService = Depends(get_database)
):
    """
    Process reference document: OCR + Parse answers.
    
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/reference/process/ref_20251022_abc123"
        ```
    """
    try:
        logger.info(f"Processing reference: {reference_id}")
        
        # Get reference from database
        ref_service = ReferenceService(db)
        reference = await ref_service.get_reference(reference_id)
        
        if not reference:
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference_id}")
        
        original_path = reference['original_reference_path']
        
        # Check if it's a PDF or image
        is_pdf = original_path.lower().endswith('.pdf')
        
        if is_pdf:
            # ===== MULTI-PAGE PDF PROCESSING =====
            logger.info("Detected PDF - Processing as multi-page document")
            from app.services.multipage_processor import MultiPageProcessor
            
            processor = MultiPageProcessor()
            result = processor.process_all_pages(
                original_path,
                reference_id,
                reference['total_marks']
            )
            
            text = result['combined_text']
            confidence = result['average_confidence']
            reference_answers = result['answers']
            
            processing_details = {
                'total_pages': result['total_pages'],
                'average_confidence': confidence,
                'processing_type': 'multi_page_pdf'
            }
            
            logger.info(f"Multi-page PDF processed: {result['total_pages']} pages, {len(reference_answers)} questions found")
            
        else:
            # ===== SINGLE IMAGE PROCESSING =====
            logger.info("Detected image - Processing as single page")
            
            # Step 1: Preprocess
            preprocessor = ImagePreprocessor()
            preprocessor.preprocess(
                original_path,
                reference['processed_reference_path']
            )
            logger.info(f"Reference preprocessed: {reference_id}")
            
            # Step 2: OCR Extract
            ocr_engine = OCREngine()
            text, confidence, _ = ocr_engine.extract_text(
                reference['processed_reference_path']
            )
            logger.info(f"Reference OCR completed: {reference_id}, Confidence: {confidence}%")
            
            # Step 3: Parse Reference Answers
            parser = AnswerParser()
            reference_answers = parser.parse(text, reference['total_marks'])
            logger.info(f"Reference parsed: {reference_id}, Found {len(reference_answers)} questions")
            
            processing_details = {
                'total_pages': 1,
                'confidence': confidence,
                'processing_type': 'single_image'
            }
        
        # ===== UPDATE DATABASE (SAME FOR BOTH) =====
        await ref_service.update_reference(reference_id, {
            "reference_text": text,
            "reference_answers": reference_answers,
            "ocr_completed": True,
            "processing_details": processing_details
        })
        
        response_data = {
            "reference_id": reference_id,
            "ocr_confidence": confidence,
            "total_questions": len(reference_answers),
            "total_pages": processing_details['total_pages'],
            "processing_type": processing_details['processing_type'],
            "reference_answers": reference_answers
        }
        
        return build_response(
            status="success",
            message="Reference processed successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reference processing failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Reference processing failed: {str(e)}",
            data=None
        )

@router.get("/list")
async def list_references(
    subject: Optional[str] = None,
    exam_name: Optional[str] = None,
    active_only: bool = True,
    db: DatabaseService = Depends(get_database)
):
    """
    List all available reference documents.
    
    Example:
        ```
        curl "http://localhost:8000/api/v1/reference/list?subject=Mathematics&active_only=true"
        ```
    """
    try:
        ref_service = ReferenceService(db)
        references = await ref_service.list_references(
            subject=subject,
            exam_name=exam_name,
            active_only=active_only
        )
        
        response_data = {
            "references": references,
            "total": len(references)
        }
        
        return build_response(
            status="success",
            message=f"Found {len(references)} references",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Reference listing failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Reference listing failed: {str(e)}",
            data=None
        )


@router.get("/{reference_id}")
async def get_reference(
    reference_id: str,
    db: DatabaseService = Depends(get_database)
):
    """
    Get details of a specific reference document.
    
    Example:
        ```
        curl "http://localhost:8000/api/v1/reference/ref_20251022_abc123"
        ```
    """
    try:
        ref_service = ReferenceService(db)
        reference = await ref_service.get_reference(reference_id)
        
        if not reference:
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference_id}")
        
        return build_response(
            status="success",
            message="Reference retrieved successfully",
            data=reference
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reference retrieval failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Reference retrieval failed: {str(e)}",
            data=None
        )


@router.delete("/{reference_id}")
async def deactivate_reference(
    reference_id: str,
    db: DatabaseService = Depends(get_database)
):
    """
    Deactivate a reference document.
    
    Example:
        ```
        curl -X DELETE "http://localhost:8000/api/v1/reference/ref_20251022_abc123"
        ```
    """
    try:
        ref_service = ReferenceService(db)
        success = await ref_service.deactivate_reference(reference_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference_id}")
        
        return build_response(
            status="success",
            message="Reference deactivated successfully",
            data={"reference_id": reference_id, "is_active": False}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reference deactivation failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Reference deactivation failed: {str(e)}",
            data=None
        )