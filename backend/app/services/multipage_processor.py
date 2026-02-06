"""
Multi-page document processing service with built-in PDF conversion.
"""
import os
from typing import List, Dict, Any
import fitz  # PyMuPDF
from PIL import Image
from app.config.logging_config import get_logger
from app.core.image_preprocessor import ImagePreprocessor
from app.core.trocr_engine import TrOCREngine
from app.core.ocr_engine import OCREngine
from app.core.answer_parser import AnswerParser

logger = get_logger(__name__)


class MultiPageProcessor:
    """Handles multi-page PDF processing with built-in conversion."""
    
    def __init__(self, use_trocr: bool = False):
        """Initialize multi-page processor."""
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = OCREngine()
        self.trocr_engine = None  # NEW: Initialize as None
        self.use_trocr = use_trocr  # NEW: Store preference
        self.parser = AnswerParser()
        # Initialize TrOCR if requested
        if use_trocr:
            logger.info("Initializing TrOCR engine for handwritten text...")
            self.trocr_engine = TrOCREngine()
        
        logger.info(f"MultiPageProcessor initialized (TrOCR: {use_trocr})")
    
    def split_pdf_to_pages(
        self,
        pdf_path: str,
        output_dir: str,
        dpi: int = 300
    ) -> List[str]:
        """
        Split PDF into individual page images using PyMuPDF.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save page images
            dpi: Resolution for conversion
            
        Returns:
            List of paths to page images
        """
        try:
            logger.info(f"Splitting PDF: {pdf_path}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            logger.info(f"PDF has {len(pdf_document)} pages")
            
            page_paths = []
            zoom = dpi / 72  # Convert DPI to zoom factor
            mat = fitz.Matrix(zoom, zoom)
            
            for page_num in range(len(pdf_document)):
                # Get page
                page = pdf_document[page_num]
                
                # Render page to pixmap
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Save as JPEG
                output_path = os.path.join(output_dir, f'page_{page_num + 1}.jpg')
                img.save(output_path, 'JPEG', quality=95)
                page_paths.append(output_path)
                
                logger.debug(f"Saved page {page_num + 1}: {output_path}")
            
            pdf_document.close()
            logger.info(f"PDF split into {len(page_paths)} page images")
            
            return page_paths
            
        except Exception as e:
            logger.error(f"PDF splitting failed: {str(e)}", exc_info=True)
            raise Exception(f"PDF splitting failed: {str(e)}")
    
    def process_all_pages(
        self,
        pdf_path: str,
        job_id: str,
        total_marks: int,
        use_handwriting_mode: bool = None
    ) -> Dict[str, Any]:
        """
        Process all pages of a PDF: preprocess, OCR, parse.
        
        Args:
            pdf_path: Path to PDF file
            job_id: Job identifier
            total_marks: Total marks for the test
            
        Returns:
            Dictionary with combined results from all pages
        """
        try:
            # Determine if we should use TrOCR
            use_trocr_for_this_job = use_handwriting_mode if use_handwriting_mode is not None else self.use_trocr
            logger.info(f"Processing multi-page PDF: {pdf_path}")
            logger.info(f"Handwriting mode: {use_trocr_for_this_job}")
            
            # Split PDF to pages
            pages_dir = os.path.join('uploads', f'{job_id}_pages')
            page_paths = self.split_pdf_to_pages(pdf_path, pages_dir)
            
            # Process each page
            all_text = []
            total_confidence = 0
            
            for i, page_path in enumerate(page_paths, start=1):
                logger.info(f"Processing page {i}/{len(page_paths)}...")
                
                # Preprocess page
                processed_path = page_path.replace('.jpg', '_processed.jpg')
                self.preprocessor.preprocess(page_path, processed_path)
                
                # Choose OCR engine based on handwriting mode
                if use_trocr_for_this_job:
                    # Use TrOCR for handwritten text
                    if self.trocr_engine is None:
                        logger.info("Lazy-loading TrOCR engine...")
                        self.trocr_engine = TrOCREngine()
                    
                    text, confidence, _ = self.trocr_engine.extract_text(processed_path)
                    logger.info(f"Page {i} TrOCR completed. Confidence: {confidence}%")
                else:
                    # Use regular Tesseract OCR
                    text, confidence, _ = self.ocr_engine.extract_text(processed_path)
                    logger.info(f"Page {i} Tesseract OCR completed. Confidence: {confidence}%")
                    
                all_text.append(text)
                total_confidence += confidence
                
                logger.info(f"Page {i} OCR completed. Confidence: {confidence}%")
            
            # Combine all text
            combined_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
            avg_confidence = total_confidence / len(page_paths)
            
            # Parse all answers from combined text
            answers = self.parser.parse(combined_text, total_marks)
            
            logger.info(f"Multi-page processing complete. Found {len(answers)} questions")
            
            return {
                'total_pages': len(page_paths),
                'combined_text': combined_text,
                'average_confidence': round(avg_confidence, 2),
                'answers': answers,
                'page_paths': page_paths
            }
            
        except Exception as e:
            logger.error(f"Multi-page processing failed: {str(e)}", exc_info=True)
            raise Exception(f"Multi-page processing failed: {str(e)}")