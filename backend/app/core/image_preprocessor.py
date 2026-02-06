"""
Image preprocessing module for denoising, resizing, and thresholding.
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any
from PIL import Image
from app.config.logging_config import get_logger

logger = get_logger(__name__)

class ImagePreprocessor:
    """
    Image preprocessor for PDFs and images.
    Simplified version for direct text extraction (no OCR preprocessing needed).
    """
    def __init__(self):
        """
        Initialize the ImagePreprocessor with optional configuration.

        Args:
            config (Dict[str, Any], optional): Configuration dictionary for preprocessing parameters.
        """
        logger.debug(f"ImagePreprocessor initialized")

    def preprocess(self, image_path: str, output_path: str, enhance_for_handwriting: bool = False) -> Dict[str, Any]:
        """
        Minimal preprocessing for direct text extraction.
        For PDFs, just copy. For images, basic validation.
        
        Args:
            image_path: Path to input file
            output_path: Path to save processed file
            
        Returns:
            Dictionary containing preprocessing details
        """
        try:
            logger.info(f"Starting preprocessing for image: {image_path}")

            # Check if it's a PDF - preprocessing.py handles PDF conversion
            if image_path.lower().endswith('.pdf'):
                import shutil
                shutil.copy2(image_path, output_path)
                
                return {
                    "preprocessing_steps": ["copy_original"],
                    "note": "No preprocessing required for PDF text extraction"
                }

            # For images, basic validation and copy
            image = cv2.imread(image_path)

            if image is None:
                raise ValueError(f"Could not read image from path: {image_path}")
            
            original_shape = image.shape
            logger.debug(f"Original image shape: {original_shape}")

            if enhance_for_handwriting:
                # Enhanced preprocessing for handwritten text
                image = self._enhance_for_handwriting(image)
                steps = ["grayscale", "denoise", "contrast_enhancement", "sharpening"]
            else:
                # Basic preprocessing
                steps = ["validation", "copy"]

            # Just save as-is (or optionally convert to grayscale)
            cv2.imwrite(output_path, image)
            
            logger.info(f"Image validated and saved: {output_path}")
            
            return {
                "original_shape": original_shape,
                "preprocessing_steps": steps,
                "enhanced_for_handwriting": enhance_for_handwriting
            }
        
        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}", exc_info=True)
            raise Exception(f"Image preprocessing failed: {str(e)}")
        
    def _enhance_for_handwriting(self, image: np.ndarray) -> np.ndarray:
        """
        Apply enhancement specifically for handwritten text.
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Sharpen the image
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(binary, -1, kernel)
        
        return sharpened
        
    # def _resize_image(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
    #     """
    #     Resize image if dimensions exceed maximum allowed.
        
    #     Args:
    #         image: Input image array
            
    #     Returns:
    #         Tuple of (resized image, resize factor)
    #     """
    #     height, width = image.shape[:2]

    #     # calculate resize factor
    #     max_dim = max(height, width)
    #     if max_dim > IMAGE_MAX_WIDTH:
    #         resize_factor = IMAGE_MAX_WIDTH / max_dim
    #         new_width = int(width * resize_factor)
    #         new_height = int(height * resize_factor)
    #         resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    #         logger.debug(f"Image resized from ({width}, {height}) to ({new_width}, {new_height})")
    #         return resized, resize_factor
        
    #     return image, 1.0
    
    # def _deskew(self, image: np.ndarray) -> np.ndarray:
    #     """
    #     Deskew image to correct rotation.
        
    #     Args:
    #         image: Input image array
            
    #     Returns:
    #         Deskewed image
    #     """
    #     try:
    #         # Calculate skew angle
    #         coords = np.column_stack(np.where(image > 0))
    #         angle = cv2.minAreaRect(coords)[-1]

    #         # Adjust angle
    #         if angle < -45:
    #             angle = -(90 + angle)
    #         else:
    #             angle = -angle
            
    #         # Rotate image if skew is significant
    #         if abs(angle) > 0.5:
    #             (h, w) = image.shape[:2]
    #             center = (w // 2, h // 2)
    #             M = cv2.getRotationMatrix2D(center, angle, 1.0)
    #             rotated = cv2.warpAffine(image, M, (w, h),
    #                                       flags=cv2.INTER_CUBIC,
    #                                       borderMode=cv2.BORDER_REPLICATE)
    #             logger.debug(f"Image deskewed by angle: {angle:.2f} degrees")
    #             return rotated
            
    #         return image
    #     except Exception as e:
    #         logger.error(f"Deskewing failed, returning original: {str(e)}")
    #         return image  # Return original if deskewing fails