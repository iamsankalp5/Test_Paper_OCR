"""
TrOCR-based OCR engine for handwritten text recognition.
Handles multi-line documents by detecting and processing individual lines.
"""
import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch
from app.config.logging_config import get_logger    

logger = get_logger(__name__)


class TrOCREngine:
    """
    TrOCR-based OCR engine optimized for handwritten text.
    Automatically segments multi-line documents and processes each line.
    """
    
    def __init__(self, model_name: str = "microsoft/trocr-base-handwritten"):
        """
        Initialize TrOCR engine.
        
        Args:
            model_name: HuggingFace model identifier
        """
        logger.info(f"Initializing TrOCR engine with model: {model_name}")
        
        try:
            self.processor = TrOCRProcessor.from_pretrained(model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
            
            # Use GPU if available
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
            logger.info(f"TrOCR engine initialized successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize TrOCR: {str(e)}")
            raise
    
    def detect_text_lines(self, image_path: str) -> List[np.ndarray]:
        """
        Detect and extract individual text lines from image.
        
        Args:
            image_path: Path to input image
            
        Returns:
            List of cropped line images
        """
        try:
            logger.info(f"Detecting text lines in: {image_path}")
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply binary threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # IMPROVED: Use horizontal kernel to connect words on same line
            # Width: 100 (connects words), Height: 1 (keeps lines separate)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (100, 1))
            dilated = cv2.dilate(binary, kernel, iterations=2)
            
            # Find contours (text lines)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Sort contours top to bottom
            contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
            
            # Extract line images
            line_images = []
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter out very small regions (noise)
                if w < 100 or h < 15:
                    continue

                if w / h < 3:  # Skip if not horizontal enough
                    continue
                
                # Add padding
                padding = 10
                y1 = max(0, y - padding)
                y2 = min(image.shape[0], y + h + padding)
                x1 = max(0, x - padding)
                x2 = min(image.shape[1], x + w + padding)
                
                # Crop line
                line_img = image[y1:y2, x1:x2]
                line_images.append(line_img)
                
                logger.debug(f"Detected line {i+1}: position=({x}, {y}), size=({w}x{h}), aspect={w/h:.1f}")
            
            logger.info(f"Detected {len(line_images)} text lines")
            return line_images
            
        except Exception as e:
            logger.error(f"Line detection failed: {str(e)}", exc_info=True)
            raise
    
    def recognize_line(self, line_image: np.ndarray) -> str:
        """
        Recognize text in a single line using TrOCR.
        
        Args:
            line_image: NumPy array of line image (OpenCV format)
            
        Returns:
            Recognized text string
        """
        try:
            # Convert OpenCV image (BGR) to PIL Image (RGB)
            if len(line_image.shape) == 3:
                line_image = cv2.cvtColor(line_image, cv2.COLOR_BGR2RGB)
            
            pil_image = Image.fromarray(line_image)
            
            # Process image
            pixel_values = self.processor(
                images=pil_image,
                return_tensors="pt"
            ).pixel_values.to(self.device)
            
            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values)
            
            # Decode text
            text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Line recognition failed: {str(e)}")
            return ""
    
    def extract_text(self, image_path: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text from multi-line handwritten document.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Tuple of (extracted_text, confidence, details)
        """
        try:
            logger.info(f"Starting TrOCR text extraction: {image_path}")
            
            # Detect text lines
            line_images = self.detect_text_lines(image_path)
            
            if not line_images:
                logger.warning("No text lines detected")
                return "", 0.0, {
                    "engine": "trocr",
                    "lines_detected": 0,
                    "text_length": 0
                }
            
            # Recognize each line
            extracted_lines = []
            for i, line_img in enumerate(line_images):
                text = self.recognize_line(line_img)
                if text:
                    extracted_lines.append(text)
                    logger.debug(f"Line {i+1}: {text[:50]}...")
            
            # Combine lines
            full_text = '\n'.join(extracted_lines)
            
            # Calculate confidence (simplified - TrOCR doesn't provide confidence scores)
            # We estimate based on successful line detection
            confidence = (len(extracted_lines) / len(line_images) * 100) if line_images else 0
            
            # Prepare details
            details = {
                "engine": "trocr",
                "model": "microsoft/trocr-base-handwritten",
                "lines_detected": len(line_images),
                "lines_recognized": len(extracted_lines),
                "text_length": len(full_text),
                "word_count": len(full_text.split()),
                "average_confidence": round(confidence, 2)
            }
            
            logger.info(f"TrOCR extraction completed: {len(extracted_lines)} lines, {len(full_text)} characters")
            
            return full_text.strip(), confidence, details
            
        except Exception as e:
            logger.error(f"TrOCR extraction failed: {str(e)}", exc_info=True)
            raise Exception(f"TrOCR extraction failed: {str(e)}")