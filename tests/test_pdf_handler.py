import pytest
from pathlib import Path
from pdf_handler import PDFHandler

def test_pdf_handler_initialization():
    handler = PDFHandler()
    assert handler is not None

def test_pdf_handler_load_invalid_file():
    handler = PDFHandler()
    assert not handler.load_pdf(Path("nonexistent.pdf"))

# Add more tests as needed
