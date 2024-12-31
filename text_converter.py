from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
from typing import Optional
from loguru import logger
import config

class TextConverter:
    """Convert PDF to text with OCR support."""
    
    def __init__(self):
        self.tesseract_available = False
        logger.info("Initializing TextConverter")
        try:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}. OCR functionality will be disabled.")
            
    def extract_text_with_ocr(self, pdf_path: Path, page_number: int) -> Optional[str]:
        """Extract text from a PDF page using OCR."""
        if not self.tesseract_available:
            logger.warning("OCR requested but Tesseract is not available")
            return None
            
        try:
            logger.info(f"Converting page {page_number} to image for OCR")
            # Convert PDF page to image
            images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
            if not images:
                logger.error(f"Failed to convert page {page_number} to image")
                return None
                
            # Convert image to text using OCR
            image = images[0]
            logger.debug(f"Running OCR on page {page_number}")
            text = pytesseract.image_to_string(image)
            if not text:
                logger.warning(f"No text extracted from page {page_number} using OCR")
            return text.strip() if text else None
            
        except Exception as e:
            logger.error(f"Error during OCR conversion of page {page_number}: {str(e)}")
            return None
            
    def is_ocr_available(self) -> bool:
        """Check if OCR functionality is available."""
        return self.tesseract_available
