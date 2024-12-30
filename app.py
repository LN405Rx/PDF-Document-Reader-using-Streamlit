# Set page config at the very start, before importing anything else
import streamlit as st
st.set_page_config(
    page_title="PDF to Audiobook Converter",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

"""
Suggested command to run the application:
streamlit run app.py
"""

import pyttsx3
import pdfplumber
import threading
from pathlib import Path
import tempfile
import os
from typing import Optional, Dict, List, Tuple, Any, Generator
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
import queue
from loguru import logger
import sys
from tenacity import retry, stop_after_attempt, wait_exponential
import psutil
import datetime
import time
import signal
from contextlib import contextmanager
from streamlit.runtime.uploaded_file_manager import UploadedFile
import pdfminer.pdfdocument
import pdfminer.pdfparser
import pdfminer.psparser
import pytesseract
from pdf2image import convert_from_path
import tempfile
from PIL import Image
import io

# Set Tesseract path - you'll need to change this to where you install Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure logging with more detailed format
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Time constants - using the provided time as source of truth
REFERENCE_TIME = datetime.datetime.fromisoformat('2024-12-13T20:28:40-06:00')

@dataclass
class AudiobookState:
    """Data class to hold the application state with improved type hints."""
    
    current_page: int = 1
    total_pages: int = 0
    is_playing: bool = False
    error_message: str = ""
    success_message: str = ""
    pdf_text: List[str] = field(default_factory=list)
    speed: int = 175
    volume: float = 1.0
    voice_idx: int = 0
    pdf: Optional[pdfplumber.PDF] = None
    text_queue: "queue.Queue[str]" = field(default_factory=lambda: queue.Queue())
    error_count: int = 0
    last_error: Optional[str] = None
    processing_futures: "List[Future[Any]]" = field(default_factory=list)
    last_settings: Dict[str, Any] = field(default_factory=lambda: {
        'speed': 200,
        'voice_index': 0,
        'speaker': 'default',
        'last_page': 1,
        'volume': 1.0,
        'chunk_size': 500,
        'last_processed_time': REFERENCE_TIME.timestamp()
    })
    cache_dir: Optional[Path] = None
    processing_lock: threading.Lock = field(default_factory=threading.Lock)
    audio_file_path: Optional[str] = None
    audio_file_name: Optional[str] = None
    audio_file_duration: Optional[int] = None
    audio_file_size: Optional[int] = None
    reading_page: int = 1

    def set_page(self, page: int) -> None:
        """Set both current page and reading page."""
        self.current_page = page
        self.reading_page = page
        # Update last settings
        self.last_settings['last_page'] = page

    def get_reading_page(self) -> int:
        """Get the current reading page."""
        return self.reading_page

class AudiobookPlayer:
    """Main class for PDF to audiobook conversion with improved performance and error handling."""
    
    def __init__(self):
        """Initialize the AudiobookPlayer with enhanced resource management."""
        if 'state' not in st.session_state:
            st.session_state.state = AudiobookState()
        elif hasattr(st.session_state.state, 'current_page'):
            # Ensure reading_page is synced with current_page on initialization
            st.session_state.state.reading_page = st.session_state.state.current_page
        
        self.engine = None
        self.voices = []
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._setup_custom_styles()
        self._setup_cache_directory()

    def init_engine(self):
        """Initialize the TTS engine with improved error handling."""
        try:
            if not hasattr(self, 'engine') or self.engine is None:
                self.engine = pyttsx3.init()
                # Set default properties
                self.engine.setProperty('rate', st.session_state.state.speed)
                self.engine.setProperty('volume', st.session_state.state.volume)
                
                # Get available voices
                voices = self.engine.getProperty('voices')
                if voices:
                    self.voices = voices
                    # Set default voice
                    self.engine.setProperty('voice', voices[st.session_state.state.voice_idx].id)
                
                logger.info("TTS engine initialized successfully")
                return True
        except Exception as e:
            self.show_error(f"Failed to initialize text-to-speech engine: {str(e)}")
            return False

    def _setup_cache_directory(self):
        """Set up a cache directory for temporary files."""
        try:
            cache_dir = Path(tempfile.gettempdir()) / "pdf_audiobook_cache"
            cache_dir.mkdir(exist_ok=True)
            st.session_state.state.cache_dir = cache_dir
        except Exception as e:
            logger.error(f"Failed to set up cache directory: {e}")
            self.show_error("Failed to set up cache directory")
    
    def _setup_custom_styles(self):
        """Setup enhanced UI styles with better visual hierarchy."""
        st.markdown("""
            <style>
                .main-title {
                    text-align: center;
                    color: #1E88E5;
                    font-size: 3em;
                    margin-bottom: 1em;
                    font-weight: 600;
                }
                .stButton>button {
                    width: 100%;
                    height: 3em;
                    font-weight: bold;
                    transition: all 0.3s ease;
                }
                .stButton>button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }
            </style>
        """, unsafe_allow_html=True)
    
    def create_ui(self):
        """Create the main Streamlit UI."""
        try:
            st.title("📚 PDF to Audiobook Converter")
            
            # Add instructions
            with st.expander("📖 How to Use", expanded=True):
                st.markdown("""
                ### Instructions:
                1. **Upload a PDF**: Click the 'Upload PDF' button below to select your PDF file.
                
                2. **Navigate Pages**:
                   - Enter a page number and click 'Go'
                   - Use ⏮️ Previous and ⏭️ Next buttons
                   - Current page text will be shown below
                
                3. **Playback Controls**:
                   - ▶️ Play: Start reading from current page
                   - ⏸️ Pause: Pause the reading
                   - Reading will automatically advance to next page
                
                4. **Customize Settings** (in sidebar):
                   - Adjust reading speed
                   - Select different voices
                   - Control volume
                """)

            # File uploader
            uploaded_file = st.file_uploader(
                "Upload PDF",
                type=['pdf'],
                help="Select a PDF file to convert to audio"
            )

            if uploaded_file is not None:
                self.handle_file_upload(uploaded_file)
                self._create_controls()
            else:
                st.info("👆 Upload a PDF file to get started!")

        except Exception as e:
            self.show_error(f"Error creating UI: {str(e)}")

    def update_page(self, new_page: int):
        """Update the current page and related state."""
        if 1 <= new_page <= st.session_state.state.total_pages:
            st.session_state.state.set_page(new_page)
            st.session_state.state.is_playing = False
            if hasattr(self, 'engine') and self.engine:
                self.engine.stop()

    def _create_controls(self):
        """Create playback controls and settings."""
        try:
            # Initialize TTS engine if needed
            if not hasattr(self, 'engine') or self.engine is None:
                self.init_engine()

            # Display current page status prominently
            st.header(f"📖 Page {st.session_state.state.current_page} of {st.session_state.state.total_pages}")

            # Create a placeholder for reading status
            reading_status = st.empty()
            if st.session_state.state.is_playing:
                reading_status.info(f"🔊 Currently reading page {st.session_state.state.current_page}")
            else:
                reading_status.info("⏸️ Playback paused")

            st.markdown("### Go to Page")
            col_page, col_goto = st.columns([3, 1])
            with col_page:
                target_page = st.number_input(
                    "Enter Page Number",
                    min_value=1,
                    max_value=st.session_state.state.total_pages,
                    value=st.session_state.state.current_page,
                    help="Enter the page number you want to start reading from",
                    key=f"target_page_input_{st.session_state.state.current_page}"  # Make key unique based on current page
                )
            with col_goto:
                if st.button("Go", use_container_width=True):
                    # Stop any current playback
                    if hasattr(self, 'engine') and self.engine:
                        self.engine.stop()
                    st.session_state.state.is_playing = False
                    self.update_page(target_page)

            # Create three columns for the main controls
            st.markdown("### Playback Controls")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("⏮️ Previous", use_container_width=True, disabled=st.session_state.state.current_page <= 1):
                    # Stop any current playback
                    if hasattr(self, 'engine') and self.engine:
                        self.engine.stop()
                    st.session_state.state.is_playing = False
                    self.update_page(st.session_state.state.current_page - 1)
            
            with col2:
                if st.button("▶️ Play" if not st.session_state.state.is_playing else "⏸️ Pause", use_container_width=True):
                    if not st.session_state.state.is_playing:
                        # Start playback from current page
                        st.session_state.state.is_playing = True
                        # Ensure reading page is synced with current page before playing
                        st.session_state.state.set_page(st.session_state.state.current_page)
                        self.play_current_page()
                    else:
                        # Stop playback
                        st.session_state.state.is_playing = False
                        if hasattr(self, 'engine') and self.engine:
                            self.engine.stop()
            
            with col3:
                if st.button("⏭️ Next", use_container_width=True, disabled=st.session_state.state.current_page >= st.session_state.state.total_pages):
                    # Stop any current playback
                    if hasattr(self, 'engine') and self.engine:
                        self.engine.stop()
                    st.session_state.state.is_playing = False
                    self.update_page(st.session_state.state.current_page + 1)

            # Progress bar for current page
            if st.session_state.state.total_pages > 0:
                progress = st.session_state.state.current_page / st.session_state.state.total_pages
                st.progress(progress, text=f"Reading Progress: {progress:.1%}")

            # Display current text with a clear heading showing the page number
            if st.session_state.state.pdf_text:
                try:
                    current_page_idx = st.session_state.state.current_page - 1
                    if 0 <= current_page_idx < len(st.session_state.state.pdf_text):
                        current_text = st.session_state.state.pdf_text[current_page_idx]
                        st.markdown("---")  # Add a separator
                        st.markdown(f"### Current Text (Page {st.session_state.state.current_page})")
                        text_container = st.container()
                        with text_container:
                            st.markdown(current_text)

                        # Handle text-to-speech
                        if st.session_state.state.is_playing:
                            self.play_current_page()
                    else:
                        st.error(f"Error: Page {st.session_state.state.current_page} is out of range")
                        st.session_state.state.is_playing = False
                        if hasattr(self, 'engine') and self.engine:
                            self.engine.stop()
                except Exception as e:
                    st.error(f"Error displaying text: {str(e)}")
                    st.session_state.state.is_playing = False
                    if hasattr(self, 'engine') and self.engine:
                        self.engine.stop()

            # Settings sidebar
            with st.sidebar:
                st.header("Settings")
                
                # Speed control
                speed = st.slider(
                    "Reading Speed",
                    min_value=100,
                    max_value=400,
                    value=int(st.session_state.state.speed),
                    step=25,
                    help="Adjust the reading speed (words per minute)"
                )
                if speed != st.session_state.state.speed:
                    st.session_state.state.speed = speed
                    if hasattr(self, 'engine') and self.engine:
                        self.engine.setProperty('rate', speed)
                
                # Voice selection
                if hasattr(self, 'voices') and self.voices:
                    voice_names = [voice.name for voice in self.voices]
                    voice_idx = st.selectbox(
                        "Voice",
                        range(len(voice_names)),
                        format_func=lambda x: voice_names[x],
                        index=st.session_state.state.voice_idx,
                        help="Select the voice for text-to-speech"
                    )
                    
                    if voice_idx != st.session_state.state.voice_idx:
                        st.session_state.state.voice_idx = voice_idx
                        if self.engine:
                            self.engine.setProperty('voice', self.voices[voice_idx].id)
                
                # Volume control
                volume = st.slider(
                    "Volume",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(st.session_state.state.volume),
                    step=0.1,
                    help="Adjust the audio volume"
                )
                if volume != st.session_state.state.volume:
                    st.session_state.state.volume = volume
                    if hasattr(self, 'engine') and self.engine:
                        self.engine.setProperty('volume', volume)

        except Exception as e:
            self.show_error(f"Error creating controls: {str(e)}")

    @contextmanager
    def error_handling(self, operation: str):
        """Context manager for handling errors in operations."""
        try:
            yield
        except Exception as e:
            logger.exception(f"Error during {operation}")
            self.show_error(f"Error during {operation}: {str(e)}")
            raise

    def handle_file_upload(self, uploaded_file: UploadedFile):
        """Handle PDF file upload with improved validation and processing."""
        try:
            # Create a temporary file to store the uploaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_path = tmp_file.name
                tmp_file.write(uploaded_file.getvalue())

            try:
                # Reset state for new file
                st.session_state.state.pdf_text = []
                st.session_state.state.total_pages = 0
                st.session_state.state.is_playing = False
                
                # Process the PDF file
                with pdfplumber.open(tmp_path) as pdf:
                    # Reset state for new file
                    st.session_state.state.pdf_text = []
                    st.session_state.state.total_pages = len(pdf.pages)
                    # Keep current page if it's within valid range, otherwise reset to 1
                    if not (1 <= st.session_state.state.current_page <= len(pdf.pages)):
                        st.session_state.state.set_page(1)
                    
                    # Extract text from each page with better error handling
                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            # Try standard text extraction first
                            text = page.extract_text()
                            if text and text.strip():
                                st.session_state.state.pdf_text.append(text.strip())
                            else:
                                # Try alternate text extraction method
                                try:
                                    # Get raw text content
                                    text = page.extract_words()
                                    if text:
                                        extracted_text = ' '.join(word['text'] for word in text)
                                        st.session_state.state.pdf_text.append(extracted_text)
                                    else:
                                        st.session_state.state.pdf_text.append(f"[Page {page_num}: No readable text found]")
                                except:
                                    st.session_state.state.pdf_text.append(f"[Page {page_num}: No readable text found]")
                        except Exception as e:
                            logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                            st.session_state.state.pdf_text.append(f"[Page {page_num}: Error extracting text]")
                    
                # Check if we got any text
                text_pages = [p for p in st.session_state.state.pdf_text if not p.startswith('[Page')]
                if not text_pages:
                    self.show_error(
                        "This PDF appears to be scanned or contains only images. "
                        "Currently, text extraction from scanned PDFs is not supported. "
                        "Please try a PDF with actual text content."
                    )
                    return
                    
                self.show_success(f"📚 Successfully loaded PDF with {len(text_pages)} readable pages")
            
            except Exception as e:
                self.show_error(f"Error processing PDF: {str(e)}")
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
                        
        except Exception as e:
            self.show_error(f"Error handling file upload: {str(e)}")

    def _validate_pdf_file(self, file_path: Path) -> bool:
        """Validate PDF file format and content."""
        try:
            # First check if file exists and has content
            if not file_path.exists():
                raise ValueError("PDF file does not exist")
            
            if file_path.stat().st_size == 0:
                raise ValueError("PDF file is empty")

            # Try to open with pdfplumber to check basic PDF validity
            try:
                with pdfplumber.open(file_path) as pdf:
                    # Check if PDF has pages
                    if len(pdf.pages) == 0:
                        raise ValueError("PDF file contains no pages")
                    return True
                    
            except Exception as e:
                if "file has not been decrypted" in str(e).lower():
                    raise ValueError("This PDF is encrypted and requires a password. Please provide an unencrypted PDF file.")
                raise ValueError(f"Error reading PDF: {str(e)}")
                
        except ValueError as e:
            self.show_error(str(e))
            return False
        except Exception as e:
            self.show_error(f"Unexpected error validating PDF: {str(e)}")
            return False

    def _extract_text_with_ocr(self, pdf_path: Path) -> List[str]:
        """Extract text from PDF using OCR if regular extraction fails."""
        try:
            # Convert PDF pages to images
            with st.spinner("Converting PDF pages to images..."):
                images = convert_from_path(pdf_path)
            
            extracted_texts = []
            total_images = len(images)
            
            # Process each page
            progress_bar = st.progress(0)
            for idx, image in enumerate(images):
                with st.spinner(f"Processing page {idx + 1} of {total_images} with OCR..."):
                    # Convert PIL image to bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Convert bytes back to PIL Image for OCR
                    img = Image.open(io.BytesIO(img_byte_arr))
                    
                    # Perform OCR
                    text = pytesseract.image_to_string(img)
                    
                    if text.strip():
                        extracted_texts.append(text.strip())
                    else:
                        extracted_texts.append("[No text found on this page]")
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / total_images)
            
            return extracted_texts
            
        except Exception as e:
            raise ValueError(f"Error during OCR: {str(e)}")

    def show_error(self, message: str):
        """Display an error message in the UI."""
        st.session_state.state.error_message = message
        st.error(message)
        
    def show_success(self, message: str):
        """Display a success message in the UI."""
        st.session_state.state.success_message = message
        st.success(message)
        
    def clear_messages(self):
        """Clear all status messages."""
        st.session_state.state.error_message = ""
        st.session_state.state.success_message = ""

    def play_current_page(self):
        """Play the current page text."""
        try:
            if not self.engine:
                if not self.init_engine():
                    return

            # Get the text from the current reading page
            current_page_idx = st.session_state.state.current_page - 1
            if 0 <= current_page_idx < len(st.session_state.state.pdf_text):
                current_text = st.session_state.state.pdf_text[current_page_idx]
                if current_text and not current_text.startswith('[No text found'):
                    # Stop any existing playback
                    if hasattr(self, 'engine') and self.engine:
                        self.engine.stop()
                    # Update engine properties
                    self.engine.setProperty('rate', st.session_state.state.speed)
                    self.engine.setProperty('volume', st.session_state.state.volume)
                    if self.voices:
                        self.engine.setProperty('voice', self.voices[st.session_state.state.voice_idx].id)
                    
                    # Update reading status before playing
                    st.info(f"🔊 Currently reading page {st.session_state.state.current_page}")
                    
                    # Play the text
                    self.engine.say(current_text)
                    self.engine.runAndWait()
                    
                    # Auto-advance to next page if available and still playing
                    if st.session_state.state.is_playing and st.session_state.state.current_page < st.session_state.state.total_pages:
                        next_page = st.session_state.state.current_page + 1
                        st.session_state.state.set_page(next_page)
                        # Update reading status for next page
                        st.info(f"🔊 Moving to page {next_page}")
                        # Play next page automatically
                        self.play_current_page()
                else:
                    st.warning("No readable text on this page")
                    st.session_state.state.is_playing = False
            else:
                st.error(f"Error: Page {st.session_state.state.current_page} is out of range")
                st.session_state.state.is_playing = False
        except Exception as e:
            self.show_error(f"Error during playback: {str(e)}")
            st.session_state.state.is_playing = False
            if self.engine:
                try:
                    self.engine.stop()
                except:
                    pass

def main():
    """Main entry point with error handling."""
    try:
        player = AudiobookPlayer()
        player.create_ui()
    except Exception as e:
        st.error(f"Application failed to start: {str(e)}")
        logger.exception("Application startup failed")

if __name__ == "__main__":
    main()
