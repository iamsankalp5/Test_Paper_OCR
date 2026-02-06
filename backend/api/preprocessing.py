"""
Image preprocessing endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.image_preprocessor import ImagePreprocessor
from app.models.schemas import PreprocessingRequest
from app.models.enums import WorkflowState
from app.core.utils import build_response
from app.config.logging_config import get_logger
import os

logger = get_logger(__name__)
router = APIRouter()


@router.post("/")
async def preprocess_image(
    request: PreprocessingRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Preprocess uploaded image for OCR.
    Handles both single images and multi-page PDFs.
    
    Args:
        request: Preprocessing request with job_id
        
    Returns:
        Preprocessing results
        
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/preprocess/" \
          -H "Content-Type: application/json" \
          -d '{"job_id": "job_20251022_abc123"}'
        ```
    """
    try:
        logger.info(f"Preprocessing requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Check if already preprocessed
        if job['state'] not in [WorkflowState.UPLOADED.value, WorkflowState.PREPROCESSING.value]:
            logger.warning(f"Job already in state: {job['state']}")
        
        # Update state to preprocessing
        await db.update_job(request.job_id, {
            "state": WorkflowState.PREPROCESSING.value,
            "current_step": "preprocessing",
            "progress_percentage": 15
        })
        
        original_path = job['original_image_path']
        is_pdf = original_path.lower().endswith('.pdf')
        
        if is_pdf:
            # ===== MULTI-PAGE PDF PREPROCESSING =====
            logger.info("Detected PDF - Converting to images and preprocessing")
            from app.services.multipage_processor import MultiPageProcessor
            
            processor = MultiPageProcessor()
            
            # Split PDF to pages
            pages_dir = os.path.join('uploads', f'{request.job_id}_pages')
            page_paths = processor.split_pdf_to_pages(original_path, pages_dir)
            
            logger.info(f"PDF split into {len(page_paths)} pages")
            
            # Preprocess all pages
            processed_pages = []
            for i, page_path in enumerate(page_paths, start=1):
                processed_path = page_path.replace('.jpg', '_processed.jpg')
                preprocessor = ImagePreprocessor()
                preprocessor.preprocess(page_path, processed_path)
                processed_pages.append(processed_path)
                logger.debug(f"Preprocessed page {i}/{len(page_paths)}")
            
            preprocessing_details = {
                'total_pages': len(page_paths),
                'page_paths': page_paths,
                'processed_pages': processed_pages,
                'processing_type': 'multi_page_pdf',
                'preprocessing_steps': [
                    'pdf_to_image_conversion',
                    'grayscale_conversion',
                    'denoising',
                    'adaptive_thresholding',
                    'deskewing',
                    'contrast_enhancement'
                ]
            }
            
            logger.info(f"Multi-page PDF preprocessing complete: {len(page_paths)} pages")
            
        else:
            # ===== SINGLE IMAGE PREPROCESSING =====
            logger.info("Detected image - Processing as single page")
            
            preprocessor = ImagePreprocessor()
            preprocessing_details = preprocessor.preprocess(
                original_path,
                job['processed_image_path']
            )
            
            preprocessing_details['total_pages'] = 1
            preprocessing_details['processing_type'] = 'single_image'
        
        # ===== UPDATE DATABASE (SAME FOR BOTH) =====
        await db.update_job(request.job_id, {
            "state": WorkflowState.PREPROCESSED.value,
            "current_step": "preprocessed",
            "progress_percentage": 20,
            "preprocessing_details": preprocessing_details
        })
        
        logger.info(f"Preprocessing completed for job: {request.job_id}")
        
        response_data = {
            "job_id": request.job_id,
            "processed_image_path": job['processed_image_path'],
            "preprocessing_details": preprocessing_details,
            "state": WorkflowState.PREPROCESSED.value
        }
        
        return build_response(
            status="success",
            message="Image preprocessing completed successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        return build_response(
            status="error",
            message=f"Preprocessing failed: {str(e)}",
            data=None
        )