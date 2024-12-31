import streamlit as st
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Union
import json
import config
from loguru import logger

from pdf_handler import PDFHandler
from audio_reader import AudioReader

@dataclass
class AppState:
    """Application state management."""
    current_page: int = 1
    total_pages: int = 0
    is_playing: bool = False
    pdf_text: List[str] = field(default_factory=list)
    speed: int = config.SPEED_DEFAULT
    volume: float = config.VOLUME_DEFAULT
    voice_idx: int = 0
    last_session: Dict[str, Any] = field(default_factory=lambda: {
        'page': 1,
        'settings': {
            'speed': config.SPEED_DEFAULT,
            'volume': config.VOLUME_DEFAULT,
            'voice': 0
        }
    })
    cache_dir: Optional[Path] = None

def save_session_state():
    """Save current session state to disk."""
    try:
        session_file = Path(config.CACHE_DIR) / "session_state.json"
        state_data = {
            'current_page': st.session_state.state.current_page,
            'speed': st.session_state.state.speed,
            'volume': st.session_state.state.volume,
            'voice_idx': st.session_state.state.voice_idx,
            'last_session': st.session_state.state.last_session
        }
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(session_file, 'w') as f:
            json.dump(state_data, f)
        logger.debug("Session state saved successfully")
    except Exception as e:
        logger.error(f"Error saving session state: {str(e)}")

def load_session_state() -> Dict[str, Any]:
    """Load previous session state from disk."""
    try:
        session_file = Path(config.CACHE_DIR) / "session_state.json"
        if session_file.exists():
            with open(session_file, 'r') as f:
                state_data = json.load(f)
            logger.info("Previous session state loaded")
            return state_data
    except Exception as e:
        logger.error(f"Error loading session state: {str(e)}")
    return {}

def initialize_app():
    """Initialize the application state."""
    if 'state' not in st.session_state:
        st.session_state.state = AppState()
        
        # Load previous session state
        previous_state = load_session_state()
        if previous_state:
            st.session_state.state.last_session = previous_state.get('last_session', {})
            st.session_state.state.speed = previous_state.get('speed', config.SPEED_DEFAULT)
            st.session_state.state.volume = previous_state.get('volume', config.VOLUME_DEFAULT)
            st.session_state.state.voice_idx = previous_state.get('voice_idx', 0)
            
        # Initialize cache directory
        cache_dir = Path(config.CACHE_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)
        st.session_state.state.cache_dir = cache_dir
        
    # Check system resources
    memory_warning = config.check_memory_usage()
    if memory_warning:
        st.warning(memory_warning)

def main():
    initialize_app()
    
    st.title("📚 PDF to Audiobook Converter")
    
    # Quick Instructions
    with st.expander("📖 How to Use", expanded=True):
        st.markdown("""
        **Quick Steps:**
        1. 📤 Upload your PDF using the sidebar
        2. 🎚️ Adjust reading speed (50-400 wpm) and volume
        3. 📄 Select starting page number
        4. ▶️ Click 'Start Reading' to begin
        5. ⏹️ Use 'Stop' to pause anytime
        
        Your progress and settings will be automatically saved.
        """)
    
    # Sidebar controls
    with st.sidebar:
        st.header("Controls")
        
        uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
        
        if uploaded_file is not None:
            pdf_handler = PDFHandler()
            
            # Save uploaded file
            temp_dir = st.session_state.state.cache_dir / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / uploaded_file.name
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            if pdf_handler.load_pdf(temp_path):
                st.session_state.state.total_pages = pdf_handler.total_pages
                st.session_state.state.pdf_text = pdf_handler.extract_all_text()
                
                # Speed control
                st.session_state.state.speed = st.slider(
                    "Reading Speed",
                    min_value=config.SPEED_MIN,
                    max_value=config.SPEED_MAX,
                    value=st.session_state.state.speed,
                    step=config.SPEED_STEP
                )
                
                # Volume control
                st.session_state.state.volume = st.slider(
                    "Volume",
                    min_value=config.VOLUME_MIN,
                    max_value=config.VOLUME_MAX,
                    value=st.session_state.state.volume,
                    step=config.VOLUME_STEP
                )
                
                # Voice selection
                audio_reader = AudioReader()
                voices = audio_reader.voices
                voice_names = [voice.name for voice in voices]
                selected_voice = st.selectbox(
                    "Select Voice",
                    options=range(len(voice_names)),
                    format_func=lambda x: voice_names[x],
                    index=st.session_state.state.voice_idx
                )
                st.session_state.state.voice_idx = selected_voice
                
                # Page selection
                page_number = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=st.session_state.state.total_pages,
                    value=st.session_state.state.current_page
                )
                
                # Control buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Start Reading"):
                        audio_reader = AudioReader()
                        audio_reader.set_properties(
                            st.session_state.state.speed,
                            st.session_state.state.volume,
                            st.session_state.state.voice_idx
                        )
                        st.session_state.state.current_page = page_number
                        st.session_state.state.is_playing = True
                        save_session_state()
                        audio_reader.read_pages(
                            st.session_state.state.pdf_text,
                            start_page=page_number
                        )
                
                with col2:
                    if st.button("Stop"):
                        st.session_state.state.is_playing = False
                        save_session_state()
    
    # Main content area
    if st.session_state.state.pdf_text:
        st.subheader(f"Page {st.session_state.state.current_page} of {st.session_state.state.total_pages}")
        if st.session_state.state.current_page <= len(st.session_state.state.pdf_text):
            st.text_area(
                "Text Content",
                st.session_state.state.pdf_text[st.session_state.state.current_page - 1],
                height=300
            )
    else:
        st.info("Please upload a PDF file to begin")
        
        # Show previous session info if available
        if st.session_state.state.last_session.get('page'):
            st.info(
                f"Previous session: Page {st.session_state.state.last_session['page']} "
                f"(Speed: {st.session_state.state.last_session['settings']['speed']})"
            )

if __name__ == "__main__":
    main()
