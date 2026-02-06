"""
Vision service for advanced computer vision operations.
"""
import cv2
import numpy as np
from typing import List, Tuple
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class VisionService:
    """Service for computer vision operations."""
    
    def __init__(self):
        """Initialize vision service."""
        logger.info("VisionService initialized")
    
    def detect_document_corners(self, image_path: str) -> List[Tuple[int, int]]:
        """
        Detect corners of a document in an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of corner coordinates
        """
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Approximate polygon
                epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                if len(approx) == 4:
                    corners = [(int(point[0][0]), int(point[0][1])) for point in approx]
                    logger.info("Document corners detected successfully")
                    return corners
            
            logger.warning("Could not detect document corners")
            return []
            
        except Exception as e:
            logger.error(f"Corner detection failed: {str(e)}")
            return []
    
    def enhance_image_quality(self, image_path: str, output_path: str) -> str:
        """
        Enhance image quality for better OCR results.
        
        Args:
            image_path: Path to input image
            output_path: Path to save enhanced image
            
        Returns:
            Path to enhanced image
        """
        try:
            image = cv2.imread(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Save enhanced image
            cv2.imwrite(output_path, enhanced)
            logger.info(f"Image enhanced successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {str(e)}")
            raise