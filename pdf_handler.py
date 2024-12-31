import pdfplumber
from pathlib import Path
from typing import List, Optional, Dict
import streamlit as st
from loguru import logger
import gc
import os
import time
import shutil
import config

class PDFHandler:
    """Handle PDF document operations."""
    
    def __init__(self):
        self.pdf = None
        self.total_pages = 0
        self.current_page = 1
        self.pdf_text = []
        self.last_cleanup = time.time()
        logger.info("Initializing PDFHandler")
        
    def load_pdf(self, file_path: Path) -> bool:
        """Load a PDF file and return success status."""
        try:
            logger.info(f"Loading PDF: {file_path}")
            self.cleanup_memory()  # Clean up before loading new PDF
            self.pdf = pdfplumber.open(file_path)
            self.total_pages = len(self.pdf.pages)
            logger.info(f"Successfully loaded PDF with {self.total_pages} pages")
            self.cleanup_cache()  # Check and clean cache if needed
            return True
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            return False
            
    def extract_text(self, page_number: int) -> Optional[str]:
        """Extract text from a specific page."""
        try:
            if not self.pdf or page_number < 1 or page_number > self.total_pages:
                logger.error(f"Invalid page number {page_number} or PDF not loaded")
                return None
            
            logger.debug(f"Extracting text from page {page_number}")
            page = self.pdf.pages[page_number - 1]
            text = page.extract_text()
            if not text:
                logger.warning(f"No text found on page {page_number}")
            
            # Check memory usage after extraction
            memory_warning = config.check_memory_usage()
            if memory_warning:
                logger.warning(memory_warning)
                self.cleanup_memory()
                
            return text if text else None
        except Exception as e:
            logger.error(f"Error extracting text from page {page_number}: {str(e)}")
            return None
            
    def extract_all_text(self) -> List[str]:
        """Extract text from all pages."""
        logger.info("Starting text extraction from all pages")
        self.pdf_text = []
        for i in range(1, self.total_pages + 1):
            text = self.extract_text(i) or ""
            self.pdf_text.append(text)
            logger.debug(f"Extracted {len(text)} characters from page {i}")
        logger.info(f"Completed text extraction from {self.total_pages} pages")
        return self.pdf_text
        
    def cleanup_memory(self):
        """Release memory after processing large PDFs."""
        logger.info("Cleaning up memory")
        if hasattr(self, 'pdf_text'):
            self.pdf_text = []
        if self.pdf:
            self.pdf.close()
            self.pdf = None
        gc.collect()
        logger.debug("Memory cleanup completed")
        
    def cleanup_cache(self):
        """Clean up old cache files."""
        try:
            if not hasattr(self, 'last_cleanup') or time.time() - self.last_cleanup < 3600:
                return  # Only check once per hour
                
            cache_dir = Path(config.CACHE_DIR)
            if not cache_dir.exists():
                return
                
            logger.info("Starting cache cleanup")
            current_time = time.time()
            total_size = 0
            
            # Remove old files and calculate total size
            for file in cache_dir.glob('*'):
                if file.is_file():
                    file_age_days = (current_time - file.stat().st_mtime) / (24 * 3600)
                    file_size_mb = file.stat().st_size / (1024 * 1024)
                    total_size += file_size_mb
                    
                    if file_age_days > config.CACHE_CLEANUP_DAYS:
                        file.unlink()
                        logger.debug(f"Removed old cache file: {file}")
                        
            # If still over size limit, remove oldest files
            if total_size > config.MAX_CACHE_SIZE_MB:
                files = sorted(cache_dir.glob('*'), key=lambda x: x.stat().st_mtime)
                for file in files:
                    if total_size <= config.MAX_CACHE_SIZE_MB:
                        break
                    if file.is_file():
                        file_size_mb = file.stat().st_size / (1024 * 1024)
                        file.unlink()
                        total_size -= file_size_mb
                        logger.debug(f"Removed cache file due to size limit: {file}")
                        
            self.last_cleanup = time.time()
            logger.info("Cache cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {str(e)}")
        
    def close(self):
        """Close the PDF file."""
        logger.info("Closing PDF file")
        self.cleanup_memory()
        logger.debug("PDF file closed successfully")
            
    def __del__(self):
        """Ensure PDF is closed on object destruction."""
        self.close()
