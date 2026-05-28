"""
Voice Engine
Manages speech recognition, text-to-speech, and wake word detection.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import queue

logger = logging.getLogger(__name__)


class VoiceState(Enum):
    """Voice engine states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceConfig:
    """Voice engine configuration"""
    wake_word: str = "illi"
    stt_model: str = "base"
    tts_model: str = "en_US-lessac-medium"
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    sensitivity: float = 0.5


class VoiceEngine:
    """
    Main voice engine that handles STT, TTS, and wake word detection.
    """
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.state = VoiceState.IDLE
        self._stt_model = None
        self._tts_engine = None
        self._wake_word_detector = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._running = False
        self._wake_word_callback: Optional[Callable] = None
        self._transcription_callback: Optional[Callable] = None
        
    async def initialize(self):
        """Initialize the voice engine"""
        logger.info("Initializing Voice Engine...")
        
        try:
            # Initialize STT (Speech-to-Text)
            await self._init_stt()
            
            # Initialize TTS (Text-to-Speech)
            await self._init_tts()
            
            # Initialize wake word detector
            await self._init_wake_word()
            
            logger.info("Voice Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Voice Engine: {e}")
            self.state = VoiceState.ERROR
            raise
    
    async def _init_stt(self):
        """Initialize speech-to-text model"""
        try:
            import whisper
            logger.info(f"Loading Whisper model: {self.config.stt_model}")
            self._stt_model = whisper.load_model(self.config.stt_model)
            logger.info("Whisper model loaded")
        except ImportError:
            logger.warning("Whisper not available, using mock STT")
            self._stt_model = "mock"
        except Exception as e:
            logger.error(f"Error loading Whisper: {e}")
            self._stt_model = "mock"
    
    async def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            
            # Configure voice
            voices = self._tts_engine.getProperty('voices')
            if voices:
                self._tts_engine.setProperty('voice', voices[0].id)
            
            self._tts_engine.setProperty('rate', 150)  # Speed
            self._tts_engine.setProperty('volume', 0.9)  # Volume
            
            logger.info("TTS engine initialized")
        except ImportError:
            logger.warning("pyttsx3 not available, using mock TTS")
            self._tts_engine = "mock"
        except Exception as e:
            logger.error(f"Error initializing TTS: {e}")
            self._tts_engine = "mock"
    
    async def _init_wake_word(self):
        """Initialize wake word detector"""
        try:
            import pvporcupine
            logger.info(f"Loading wake word detector for: {self.config.wake_word}")
            # Porcupine requires an access key
            # For now, use a simple keyword matching approach
            self._wake_word_detector = "simple"
            logger.info("Wake word detector initialized")
        except ImportError:
            logger.warning("Porcupine not available, using simple wake word detection")
            self._wake_word_detector = "simple"
        except Exception as e:
            logger.error(f"Error initializing wake word detector: {e}")
            self._wake_word_detector = "simple"
    
    async def start_listening(self, continuous: bool = False):
        """Start listening for audio input"""
        if self.state == VoiceState.LISTENING:
            logger.warning("Already listening")
            return
        
        self.state = VoiceState.LISTENING
        logger.info("Started listening")
        
        if continuous:
            asyncio.create_task(self._continuous_listen_loop())
    
    async def stop_listening(self):
        """Stop listening for audio input"""
        self.state = VoiceState.IDLE
        logger.info("Stopped listening")
    
    async def _continuous_listen_loop(self):
        """Continuous listening loop for wake word detection"""
        while self.state == VoiceState.LISTENING:
            try:
                # In a real implementation, this would capture audio
                # and process it for wake word detection
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                await asyncio.sleep(1)
    
    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Transcribed text
        """
        if self.state != VoiceState.IDLE:
            self.state = VoiceState.PROCESSING
        
        try:
            if self._stt_model == "mock":
                return "[MOCK TRANSCRIPTION] This is simulated speech recognition"
            
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            result = self._stt_model.transcribe(audio_array)
            text = result["text"].strip()
            
            logger.info(f"Transcribed: {text}")
            
            if self._transcription_callback:
                await self._transcription_callback(text)
            
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
        finally:
            self.state = VoiceState.IDLE
    
    async def speak(self, text: str, emotion: str = "neutral"):
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            emotion: Emotion to apply (neutral, happy, sad, etc.)
        """
        if self.state != VoiceState.IDLE:
            logger.warning("Cannot speak while busy")
            return
        
        self.state = VoiceState.SPEAKING
        logger.info(f"Speaking: {text[:50]}...")
        
        try:
            if self._tts_engine == "mock":
                logger.info(f"[MOCK TTS] Would speak: {text}")
                await asyncio.sleep(len(text) * 0.05)  # Simulate speaking time
            else:
                # Apply emotion-based modifications
                modified_text = self._apply_emotion(text, emotion)
                
                # Speak using pyttsx3
                self._tts_engine.say(modified_text)
                self._tts_engine.runAndWait()
            
            logger.info("Finished speaking")
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self.state = VoiceState.IDLE
    
    def _apply_emotion(self, text: str, emotion: str) -> str:
        """Apply emotion modifications to text"""
        # Simple emotion simulation
        if emotion == "happy":
            # Add enthusiasm markers
            return text + "!"
        elif emotion == "sad":
            # Add softer tone markers
            return text
        elif emotion == "excited":
            # Add emphasis
            return text.upper()
        else:
            return text
    
    def set_wake_word_callback(self, callback: Callable):
        """Set callback for wake word detection"""
        self._wake_word_callback = callback
    
    def set_transcription_callback(self, callback: Callable):
        """Set callback for transcription results"""
        self._transcription_callback = callback
    
    async def check_wake_word(self, text: str) -> bool:
        """
        Check if text contains wake word.
        
        Args:
            text: Text to check
            
        Returns:
            True if wake word detected
        """
        wake_word_lower = self.config.wake_word.lower()
        text_lower = text.lower()
        
        detected = wake_word_lower in text_lower
        
        if detected and self._wake_word_callback:
            await self._wake_word_callback(text)
        
        return detected
    
    async def process_audio_stream(self, audio_chunk: bytes):
        """
        Process a chunk of audio from a stream.
        
        Args:
            audio_chunk: Audio data chunk
        """
        self._audio_queue.put(audio_chunk)
    
    async def get_state(self) -> VoiceState:
        """Get current voice engine state"""
        return self.state
    
    async def stop(self):
        """Stop the voice engine"""
        self._running = False
        self.state = VoiceState.IDLE
        logger.info("Voice Engine stopped")


class VoiceAssistant:
    """
    High-level voice assistant that coordinates voice interactions.
    """
    
    def __init__(self, voice_engine: VoiceEngine):
        self.voice_engine = voice_engine
        self._conversation_history: list = []
        
    async def initialize(self):
        """Initialize the voice assistant"""
        await self.voice_engine.initialize()
        
        # Set up callbacks
        self.voice_engine.set_wake_word_callback(self._on_wake_word)
        self.voice_engine.set_transcription_callback(self._on_transcription)
    
    async def _on_wake_word(self, text: str):
        """Handle wake word detection"""
        logger.info(f"Wake word detected: {text}")
        # Trigger listening for command
    
    async def _on_transcription(self, text: str):
        """Handle transcription result"""
        logger.info(f"Transcription received: {text}")
        self._conversation_history.append({"role": "user", "content": text})
    
    async def listen_and_respond(self, query_handler: Callable) -> str:
        """
        Listen for user input, process it, and respond.
        
        Args:
            query_handler: Function to handle the user query
            
        Returns:
            Response text
        """
        # Listen for input
        await self.voice_engine.start_listening()
        
        # In a real implementation, this would capture actual audio
        # For now, simulate
        user_input = "Hello ILLI"
        
        await self.voice_engine.stop_listening()
        
        # Process query
        response = await query_handler(user_input)
        
        # Speak response
        await self.voice_engine.speak(response)
        
        self._conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def get_conversation_history(self) -> list:
        """Get conversation history"""
        return self._conversation_history
    
    async def stop(self):
        """Stop the voice assistant"""
        await self.voice_engine.stop()
