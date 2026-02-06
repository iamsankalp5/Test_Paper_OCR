"""
OCR extraction engine supporting Tesseract and EasyOCR.
"""

import pytesseract
import easyocr
from typing import List, Dict, Any, Tuple
import cv2
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.config.constants import OCR_MIN_CONFIDENCE

logger = get_logger(__name__)

# Set Tesseract command path
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

class OCREngine:
    """Handles OCR text extraction from images."""

    def __init__(self):
        """Initialize OCR engine."""
        self.easyocr_reader = None
        logger.info("OCREngine initialized")

    def extract_text_tesseract(self, image_path: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text using Tesseract OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, confidence, details)
            
        Raises:
            Exception: If OCR extraction fails
        """
        try:
            logger.info(f"Starting Tesseract OCR for: {image_path}")

            # Read Image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from path: {image_path}")
            
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6'

            # Extract Text
            text = pytesseract.image_to_string(image, config=custom_config)
            logger.debug(f"Extracted text length: {len(text)} characters")

            # Get detailed OCR data for confidence calculation
            data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)

            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            logger.info(f"Tesseract OCR completed with average confidence: {avg_confidence:.2f}%")

            # Prepare details
            details = {
                "engine": "tesseract",
                "config": custom_config,
                "text_length": len(text),
                "word_count": len(text.split()),
                "average_confidence": round(avg_confidence, 2),
                "low_confidence_words": sum(1 for conf in confidences if conf < OCR_MIN_CONFIDENCE)
            }

            return text.strip(), avg_confidence, details
        
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {str(e)}", exc_info=True)
            raise Exception(f"Tesseract OCR extraction failed: {str(e)}")
        
    def extract_text_easyocr(self, image_path: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text using EasyOCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, confidence, details)
            
        Raises:
            Exception: If OCR extraction fails
        """
        try:
            logger.info(f"Starting EasyOCR for: {image_path}")
            
            # Initialize EasyOCR reader if not already done
            if self.easyocr_reader is None:
                logger.debug("Initializing EasyOCR reader...")
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.debug("EasyOCR reader initialized")

            # Extract Text
            results = self.easyocr_reader.readtext(image_path)

            # Combine all text and calculate average confidence
            extracted_texts = []
            confidences = []

            for (bbox, text, conf) in results:
                extracted_texts.append(text)
                confidences.append(conf * 100)  # Convert to percentage

            full_text = ' '.join(extracted_texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            logger.info(f"EasyOCR completed with average confidence: {avg_confidence:.2f}%")

            # Prepare details
            details = {
                "engine": "easyocr",
                "text_length": len(full_text),
                "word_count": len(full_text.split()),
                "average_confidence": round(avg_confidence, 2),
                "detected_text_blocks": len(results),
                "low_confidence_words": sum(1 for conf in confidences if conf < OCR_MIN_CONFIDENCE)
            }

            return full_text.strip(), avg_confidence, details
        
        except Exception as e:
            logger.error(f"EasyOCR failed: {str(e)}", exc_info=True)
            raise Exception(f"EasyOCR extraction failed: {str(e)}")
        
    def extract_text_trocr(self, image_path: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text using TrOCR (optimized for handwritten text).
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, confidence, details)
        """
        try:
            logger.info(f"Starting TrOCR for: {image_path}")
            
            # Initialize TrOCR engine if not already done
            if self.trocr_engine is None:
                logger.debug("Initializing TrOCR engine...")
                from app.core.trocr_engine import TrOCREngine
                self.trocr_engine = TrOCREngine()
                logger.debug("TrOCR engine initialized")
            
            # Extract text
            text, confidence, details = self.trocr_engine.extract_text(image_path)
            
            logger.info(f"TrOCR completed: {details['lines_recognized']} lines recognized")
            
            return text, confidence, details
            
        except Exception as e:
            logger.error(f"TrOCR failed: {str(e)}", exc_info=True)
            raise Exception(f"TrOCR extraction failed: {str(e)}")
        
    def extract_text(self, image_path: str, use_easyocr: bool = False, use_trocr: bool = False) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text using specified OCR engine.
        
        Args:
            image_path: Path to image file
            use_easyocr: Use EasyOCR instead of Tesseract
            
        Returns:
            Tuple of (extracted_text, confidence, details)
        """
        if use_trocr:
            return self.extract_text_trocr(image_path)
        elif use_easyocr:
            return self.extract_text_easyocr(image_path)
        else:
            return self.extract_text_tesseract(image_path)