import pyttsx3
from typing import List, Optional, Dict
import streamlit as st
from loguru import logger
import config
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class AudioReader:
    """Handle text-to-speech functionality."""
    
    def __init__(self):
        self.engine = None
        self.voices = []
        self.is_playing = False
        self.current_page = 1
        self.error_count = 0
        self.last_error_time = 0
        self.recovery_attempts = 0
        logger.info("Initializing AudioReader")
        self.initialize_engine()
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def initialize_engine(self) -> bool:
        """Initialize the text-to-speech engine with retry logic."""
        try:
            self.engine = pyttsx3.init()
            self.voices = self.engine.getProperty('voices')
            self.engine.setProperty('rate', config.SPEED_DEFAULT)
            self.engine.setProperty('volume', config.VOLUME_DEFAULT)
            self.error_count = 0
            logger.info("Text-to-speech engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing text-to-speech engine: {str(e)}")
            self.error_count += 1
            raise
            
    def recover_playback(self) -> bool:
        """Attempt to recover from TTS engine errors."""
        try:
            logger.info("Attempting playback recovery")
            current_time = time.time()
            
            # Limit recovery attempts
            if current_time - self.last_error_time < 60:  # Within last minute
                self.recovery_attempts += 1
                if self.recovery_attempts > 3:
                    logger.error("Too many recovery attempts in short period")
                    return False
            else:
                self.recovery_attempts = 1
                
            self.last_error_time = current_time
            
            # Stop current engine
            if self.engine:
                try:
                    self.engine.stop()
                except:
                    pass
                    
            # Reinitialize engine
            return self.initialize_engine()
            
        except Exception as e:
            logger.error(f"Error during playback recovery: {str(e)}")
            return False
            
    def set_properties(self, speed: int, volume: float, voice_idx: int):
        """Set the engine properties."""
        if not self.engine:
            logger.error("Cannot set properties: Engine not initialized")
            return
            
        try:
            self.engine.setProperty('rate', speed)
            self.engine.setProperty('volume', volume)
            if self.voices and 0 <= voice_idx < len(self.voices):
                self.engine.setProperty('voice', self.voices[voice_idx].id)
            logger.debug(f"Engine properties set: speed={speed}, volume={volume}, voice={voice_idx}")
        except Exception as e:
            logger.error(f"Error setting engine properties: {str(e)}")
            self.recover_playback()
            
    def read_text(self, text: str) -> bool:
        """Read the given text."""
        if not self.engine or not text:
            logger.error("Cannot read text: Engine not initialized or text is empty")
            return False
            
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Error during text reading: {str(e)}")
            if self.recover_playback():
                # Retry once after recovery
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                    return True
                except:
                    pass
            return False
            
    def read_pages(self, texts: List[str], start_page: int = 1):
        """Read multiple pages of text continuously."""
        if not texts:
            logger.error("No texts provided for reading")
            return
            
        self.is_playing = True
        self.current_page = start_page
        logger.info(f"Starting continuous reading from page {start_page}")
        
        while self.is_playing and self.current_page <= len(texts):
            text = texts[self.current_page - 1]
            if text and not text.startswith('[No text found'):
                st.info(f"🔊 Reading page {self.current_page}")
                logger.debug(f"Reading page {self.current_page}")
                success = self.read_text(text)
                if not success:
                    logger.error(f"Failed to read page {self.current_page}")
                    if not self.recover_playback():
                        break
            else:
                logger.warning(f"Skipping page {self.current_page}: No valid text")
                
            self.current_page += 1
            
        self.is_playing = False
        if self.current_page > len(texts):
            logger.info("Finished reading all pages")
            st.success("Finished reading all pages")
            
    def stop(self):
        """Stop the current reading."""
        logger.info("Stopping audio playback")
        self.is_playing = False
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                logger.error(f"Error stopping engine: {str(e)}")
                
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up AudioReader resources")
        self.stop()
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
