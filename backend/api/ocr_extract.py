"""
OCR text extraction endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.ocr_engine import OCREngine
from app.models.schemas import OCRRequest
from app.models.enums import WorkflowState
from app.core.utils import build_response
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/")
async def extract_text_ocr(
    request: OCRRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Extract text from preprocessed image or multi-page PDF using OCR.
    
    Args:
        request: OCR request with job_id and engine selection
        
    Returns:
        Extracted text and confidence score
        
    Example:
        ```
        curl -X POST "http://localhost:8000/api/v1/ocr/" \
          -H "Content-Type: application/json" \
          -d '{"job_id": "job_20251022_abc123", "use_easyocr": false}'
        ```
    """
    try:
        logger.info(f"OCR extraction requested for job: {request.job_id}")
        
        # Get job from database
        job = await db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
        
        # Validate state
        if job['state'] != WorkflowState.PREPROCESSED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Job must be preprocessed first. Current state: {job['state']}"
            )
        
        # Update state to extracting
        await db.update_job(request.job_id, {
            "state": WorkflowState.OCR_EXTRACTING.value,
            "current_step": "ocr_extracting",
            "progress_percentage": 30
        })
        
        # Check if this is a multi-page PDF job
        preprocessing_details = job.get('preprocessing_details', {})
        is_multipage = preprocessing_details.get('processing_type') == 'multi_page_pdf'
        
        if is_multipage:
            # ===== MULTI-PAGE PDF OCR =====
            logger.info("Processing multi-page PDF OCR")
            
            processed_pages = preprocessing_details.get('processed_pages', [])
            if not processed_pages:
                raise Exception("Multi-page job but no processed pages found")
            
            ocr_engine = OCREngine()
            all_text = []
            total_confidence = 0

            # Get TrOCR option from request
            use_trocr = getattr(request, 'use_trocr', False)
            
            for i, page_path in enumerate(processed_pages, start=1):
                logger.info(f"OCR processing page {i}/{len(processed_pages)}")
                text, confidence, _ = ocr_engine.extract_text(
                    page_path,
                    use_easyocr=request.use_easyocr
                )
                all_text.append(text)
                total_confidence += confidence
                logger.info(f"Page {i} OCR complete. Confidence: {confidence}%")

            # Calculate average and retry with TrOCR if needed
            avg_confidence = total_confidence / len(processed_pages)

            if avg_confidence < 80 and not use_trocr:
                logger.info("Low confidence detected, retrying all pages with TrOCR...")
                all_text = []
                total_confidence = 0
                
                for i, page_path in enumerate(processed_pages, start=1):
                    logger.info(f"TrOCR processing page {i}/{len(processed_pages)}")
                    text, confidence, _ = ocr_engine.extract_text(
                        page_path,
                        use_trocr=True
                    )
                    all_text.append(text)
                    total_confidence += confidence
                    logger.info(f"Page {i} TrOCR complete. Confidence: {confidence}%")
                
                avg_confidence = total_confidence / len(processed_pages)
                logger.info(f"TrOCR retry completed with avg confidence: {avg_confidence}%")
            
            # Combine all text
            combined_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
            avg_confidence = total_confidence / len(processed_pages)
            
            ocr_details = {
                'total_pages': len(processed_pages),
                'average_confidence': round(avg_confidence, 2),
                'engine': 'easyocr' if request.use_easyocr else 'tesseract',
                'processing_type': 'multi_page_pdf'
            }
            
            logger.info(f"Multi-page OCR complete. Avg confidence: {avg_confidence}%")
            
        else:
            # ===== SINGLE IMAGE OCR =====
            logger.info("Processing single image OCR")

            # Get TrOCR option from request
            use_trocr = getattr(request, 'use_trocr', False)
            
            ocr_engine = OCREngine()
            combined_text, avg_confidence, ocr_details = ocr_engine.extract_text(
                job['processed_image_path'],
                use_easyocr=request.use_easyocr,
                use_trocr=use_trocr
            )

            # Auto-retry with TrOCR if confidence is low
            if avg_confidence < 80 and not use_trocr:
                logger.info("Low confidence detected, retrying with TrOCR...")
                combined_text, avg_confidence, ocr_details = ocr_engine.extract_text(
                    job['processed_image_path'],
                    use_trocr=True
                )
                logger.info(f"TrOCR retry completed with confidence: {avg_confidence}%")
            
            ocr_details['processing_type'] = 'single_image'
        
        # ===== UPDATE DATABASE (SAME FOR BOTH) =====
        await db.update_job(request.job_id, {
            "state": WorkflowState.OCR_EXTRACTED.value,
            "current_step": "ocr_extracted",
            "progress_percentage": 40,
            "extracted_text": combined_text,
            "ocr_confidence": avg_confidence,
            "ocr_details": ocr_details
        })
        
        logger.info(f"OCR extraction completed for job: {request.job_id}")
        
        response_data = {
            "job_id": request.job_id,
            "extracted_text": combined_text,
            "confidence": avg_confidence,
            "ocr_details": ocr_details,
            "state": WorkflowState.OCR_EXTRACTED.value
        }
        
        return build_response(
            status="success",
            message="OCR text extraction completed successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
        await db.update_job(request.job_id, {
            "state": WorkflowState.FAILED.value,
            "error_message": str(e)
        })
        return build_response(
            status="error",
            message=f"OCR extraction failed: {str(e)}",
            data=None
        )