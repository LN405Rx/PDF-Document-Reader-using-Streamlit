import streamlit as st
import os
import sys
import psutil
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="PDF to Audiobook Converter",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File and path configurations
CACHE_DIR = "cache"
TESSERACT_PATH = os.path.join(os.path.dirname(sys.executable), 'pytesseract.exe')

# Default settings
SPEED_DEFAULT = 175
SPEED_MIN = 50
SPEED_MAX = 400
SPEED_STEP = 25

VOLUME_DEFAULT = 1.0
VOLUME_MIN = 0.0
VOLUME_MAX = 1.0
VOLUME_STEP = 0.1

# Cache management
CACHE_CLEANUP_DAYS = 7  # Number of days to keep cache files
MAX_CACHE_SIZE_MB = 500  # Maximum cache size in MB

# Resource monitoring
MEMORY_THRESHOLD_MB = 1000  # Warning threshold for memory usage

def check_memory_usage():
    """Check current memory usage and return warning if above threshold."""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    if memory_mb > MEMORY_THRESHOLD_MB:
        return f"Warning: High memory usage ({memory_mb:.1f}MB)"
    return None
