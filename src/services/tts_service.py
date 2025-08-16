#!/usr/bin/env python3
"""
Text-to-Speech Service
Professional TTS service with multiple engine support
"""

import os
import sys
import logging
import tempfile
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSEngine(ABC):
    """Abstract base class for TTS engines"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the TTS engine"""
        pass
    
    @abstractmethod
    def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize text to speech and return audio bytes"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        pass

class Pyttsx3Engine(TTSEngine):
    """pyttsx3-based TTS engine"""
    
    def __init__(self):
        self.engine = None
        self.voices = []
        self.default_voice = None
        
    def initialize(self) -> bool:
        """Initialize pyttsx3 engine"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Get available voices
            self.voices = [voice.id for voice in self.engine.getProperty('voices')]
            if self.voices:
                self.default_voice = self.voices[0]
                self.engine.setProperty('voice', self.default_voice)
            
            # Set properties for better quality
            self.engine.setProperty('rate', 150)    # Speed
            self.engine.setProperty('volume', 0.9)  # Volume
            
            logger.info(f"✅ Pyttsx3 initialized with {len(self.voices)} voices")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize pyttsx3: {e}")
            return False
    
    def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize text to speech and return AIFF audio bytes"""
        if not self.engine:
            raise RuntimeError("TTS engine not initialized")
        
        try:
            # Set voice if specified
            if voice and voice in self.voices:
                self.engine.setProperty('voice', voice)
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Save audio to temporary file
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            
            # Read the generated audio file
            with open(temp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            logger.info(f"✅ Synthesized {len(text)} characters to {len(audio_data)} bytes AIFF")
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            raise RuntimeError(f"TTS synthesis failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.voices

class TextToSpeechService:
    """Main TTS service with multiple engine support"""
    
    def __init__(self):
        self.engines: Dict[str, TTSEngine] = {}
        self.current_engine = None
        self.engine_name = None
        
    def add_engine(self, name: str, engine: TTSEngine) -> bool:
        """Add a TTS engine"""
        if engine.initialize():
            self.engines[name] = engine
            if not self.current_engine:
                self.current_engine = engine
                self.engine_name = name
            logger.info(f"✅ Added TTS engine: {name}")
            return True
        return False
    
    def set_engine(self, name: str) -> bool:
        """Set the current TTS engine"""
        if name in self.engines:
            self.current_engine = self.engines[name]
            self.engine_name = name
            logger.info(f"✅ Switched to TTS engine: {name}")
            return True
        logger.warning(f"⚠️ TTS engine not found: {name}")
        return False
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engine names"""
        return list(self.engines.keys())
    
    def get_current_engine(self) -> Optional[str]:
        """Get current engine name"""
        return self.engine_name
    
    def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize text using current engine"""
        if not self.current_engine:
            raise RuntimeError("No TTS engine available")
        return self.current_engine.synthesize(text, voice)
    
    def synthesize_to_wav_bytes(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize text to speech and return WAV audio bytes (no conversion)"""
        try:
            # Synthesize with current engine (returns AIFF bytes)
            audio_bytes = self.current_engine.synthesize(text, voice)
            
            # Convert AIFF to WAV for better compatibility
            try:
                import io
                from pydub import AudioSegment
                
                # Load audio from AIFF bytes
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="aiff")
                
                # Export as WAV
                wav_buffer = io.BytesIO()
                audio.export(wav_buffer, format="wav")
                wav_buffer.seek(0)
                
                wav_data = wav_buffer.read()
                logger.info(f"✅ Converted AIFF to WAV: {len(wav_data)} bytes")
                return wav_data
                
            except ImportError:
                logger.warning("⚠️ pydub not available, returning AIFF format")
                return audio_bytes
            except Exception as e:
                logger.warning(f"⚠️ WAV conversion failed: {e}, returning AIFF")
                return audio_bytes
                
        except Exception as e:
            logger.exception("❌ TTS synthesis failed")
            raise RuntimeError(f"TTS synthesis failed: {e}")
    
    def synthesize_to_mp3_bytes(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize text to speech and return WAV audio bytes for maximum browser compatibility"""
        try:
            # Synthesize with current engine (returns AIFF bytes)
            audio_bytes = self.current_engine.synthesize(text, voice)
            
            # Convert AIFF to WAV for better browser compatibility
            try:
                import io
                from pydub import AudioSegment
                
                # Load audio from AIFF bytes
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="aiff")
                
                # Export as WAV with browser-compatible settings
                wav_buffer = io.BytesIO()
                audio.export(wav_buffer, format="wav", parameters=[
                    "-ar", "22050",  # Sample rate
                    "-ac", "1",      # Mono
                    "-b:a", "64k"    # Bitrate
                ])
                wav_buffer.seek(0)
                
                wav_data = wav_buffer.read()
                logger.info(f"✅ Converted AIFF to WAV: {len(wav_data)} bytes")
                return wav_data
                
            except ImportError:
                logger.warning("⚠️ pydub not available, trying FFmpeg fallback")
                return self._ffmpeg_fallback(audio_bytes, "wav")
            except Exception as e:
                logger.warning(f"⚠️ pydub conversion failed: {e}, trying FFmpeg fallback")
                return self._ffmpeg_fallback(audio_bytes, "wav")
                
        except Exception as e:
            logger.exception("❌ TTS synthesis failed")
            raise RuntimeError(f"TTS synthesis failed: {e}")
    
    def _ffmpeg_fallback(self, audio_bytes: bytes, target_format: str) -> bytes:
        """FFmpeg fallback for audio conversion"""
        try:
            import subprocess
            import tempfile
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as aiff_file:
                aiff_path = aiff_file.name
                aiff_file.write(audio_bytes)
            
            with tempfile.NamedTemporaryFile(suffix=f'.{target_format}', delete=False) as output_file:
                output_path = output_file.name
            
            # Use FFmpeg with simple settings
            if target_format == "wav":
                cmd = [
                    'ffmpeg', '-y',
                    '-i', aiff_path,
                    '-acodec', 'pcm_s16le',  # Standard WAV codec
                    '-ar', '22050',           # Sample rate
                    '-ac', '1',               # Mono
                    output_path
                ]
            else:  # MP3
                cmd = [
                    'ffmpeg', '-y',
                    '-i', aiff_path,
                    '-acodec', 'libmp3lame',
                    '-ab', '64k',
                    '-ar', '22050',
                    '-ac', '1',
                    output_path
                ]
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Read output file
                with open(output_path, 'rb') as output_file:
                    output_data = output_file.read()
                
                # Clean up temporary files
                os.unlink(aiff_path)
                os.unlink(output_path)
                
                logger.info(f"✅ FFmpeg conversion to {target_format.upper()}: {len(output_data)} bytes")
                return output_data
            else:
                logger.warning(f"⚠️ FFmpeg conversion failed: {result.stderr}")
                # Clean up and return original
                os.unlink(aiff_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return audio_bytes
                
        except Exception as e:
            logger.warning(f"⚠️ FFmpeg fallback failed: {e}")
            return audio_bytes

# Factory function to create TTS service
def create_tts_service() -> TextToSpeechService:
    """Create and configure TTS service with available engines"""
    service = TextToSpeechService()
    
    # Try to add pyttsx3 engine
    try:
        pyttsx3_engine = Pyttsx3Engine()
        service.add_engine("pyttsx3", pyttsx3_engine)
    except Exception as e:
        logger.warning(f"⚠️ Could not add pyttsx3 engine: {e}")
    
    if not service.engines:
        logger.error("❌ No TTS engines available")
        raise RuntimeError("No TTS engines available")
    
    return service

# For direct testing
if __name__ == "__main__":
    try:
        tts_service = create_tts_service()
        print(f"✅ TTS Service created with engines: {tts_service.get_available_engines()}")
        
        # Test synthesis
        test_text = "Hello, this is a test of the TTS service."
        audio_bytes = tts_service.synthesize_to_wav_bytes(test_text)
        print(f"✅ Test synthesis successful: {len(audio_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ TTS Service test failed: {e}")
