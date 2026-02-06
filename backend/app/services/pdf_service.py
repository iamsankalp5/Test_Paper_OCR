"""
PDF service for advanced PDF operations.
"""
import os
from typing import List
from PyPDF2 import PdfMerger, PdfReader
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class PDFService:
    """Service for PDF manipulation operations."""
    
    def __init__(self):
        """Initialize PDF service."""
        logger.info("PDFService initialized")
    
    def merge_pdfs(self, pdf_files: List[str], output_path: str) -> str:
        """
        Merge multiple PDF files into one.
        
        Args:
            pdf_files: List of PDF file paths
            output_path: Output path for merged PDF
            
        Returns:
            Path to merged PDF
            
        Raises:
            Exception: If merge fails
        """
        try:
            logger.info(f"Merging {len(pdf_files)} PDFs")
            
            merger = PdfMerger()
            
            for pdf_file in pdf_files:
                if os.path.exists(pdf_file):
                    merger.append(pdf_file)
                else:
                    logger.warning(f"PDF file not found: {pdf_file}")
            
            merger.write(output_path)
            merger.close()
            
            logger.info(f"PDFs merged successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF merge failed: {str(e)}", exc_info=True)
            raise Exception(f"PDF merge failed: {str(e)}")
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get information about a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF information
        """
        try:
            reader = PdfReader(pdf_path)
            info = {
                'num_pages': len(reader.pages),
                'metadata': reader.metadata,
                'file_size': os.path.getsize(pdf_path)
            }
            logger.debug(f"PDF info retrieved: {pdf_path}")
            return info
        except Exception as e:
            logger.error(f"Failed to get PDF info: {str(e)}")
            return {}