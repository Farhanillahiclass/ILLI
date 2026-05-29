"""
Local Cognition & Multi-Voice Engine Core
Long-term memory, adaptive microphone calibration, voice synthesis, deletion protection
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import threading

logger = logging.getLogger(__name__)


class LocalMemorySystem:
    """
    Long-term preference and context memory using SQLite + JSON
    Persists user preferences, voice profiles, and interaction history
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".illi_memory" / "cognition.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    type TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    voice_type TEXT,
                    pitch REAL,
                    rate REAL,
                    volume REAL,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interaction_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    input_type TEXT,
                    input_text TEXT,
                    response_text TEXT,
                    status TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mic_calibration (
                    calibration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ambient_noise_level REAL,
                    calibrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    environment TEXT
                )
            """)
            
            conn.commit()
        
        logger.info(f"Memory system initialized: {self.db_path}")
    
    def set_preference(self, key: str, value: Any, value_type: str = "string") -> bool:
        """Set user preference in memory"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    json_value = json.dumps(value) if not isinstance(value, str) else value
                    conn.execute(
                        "INSERT OR REPLACE INTO preferences (key, value, type) VALUES (?, ?, ?)",
                        (key, json_value, value_type)
                    )
                    conn.commit()
            logger.info(f"Preference set: {key}={value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set preference: {str(e)}")
            return False
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieve user preference from memory"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT value, type FROM preferences WHERE key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        value, value_type = row
                        if value_type != "string":
                            return json.loads(value)
                        return value
        except Exception as e:
            logger.error(f"Failed to get preference: {str(e)}")
        
        return default
    
    def update_voice_preference(self, call_name: str):
        """Update how the user wants to be called"""
        self.set_preference("user_call_name", call_name, "string")
        logger.info(f"Voice preference updated: Call user '{call_name}'")
    
    def get_voice_preference(self) -> str:
        """Get user's preferred call name"""
        return self.get_preference("user_call_name", "Sir")
    
    def add_interaction_record(self, input_type: str, input_text: str, 
                               response_text: str, status: str = "success", 
                               metadata: Optional[Dict] = None) -> bool:
        """Log interaction for context learning"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    metadata_json = json.dumps(metadata or {})
                    conn.execute(
                        """INSERT INTO interaction_history 
                           (input_type, input_text, response_text, status, metadata)
                           VALUES (?, ?, ?, ?, ?)""",
                        (input_type, input_text, response_text, status, metadata_json)
                    )
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to record interaction: {str(e)}")
            return False
    
    def get_interaction_history(self, limit: int = 20) -> List[Dict]:
        """Retrieve recent interaction history"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        """SELECT timestamp, input_type, input_text, response_text, status
                           FROM interaction_history
                           ORDER BY history_id DESC
                           LIMIT ?""",
                        (limit,)
                    )
                    rows = cursor.fetchall()
                    return [
                        {
                            "timestamp": row[0],
                            "input_type": row[1],
                            "input_text": row[2],
                            "response_text": row[3],
                            "status": row[4],
                        }
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to retrieve history: {str(e)}")
            return []
    
    def store_mic_calibration(self, ambient_noise_level: float, environment: str = "unknown"):
        """Store microphone calibration data"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """INSERT INTO mic_calibration (ambient_noise_level, environment)
                           VALUES (?, ?)""",
                        (ambient_noise_level, environment)
                    )
                    conn.commit()
            logger.info(f"Mic calibration stored: {ambient_noise_level} dB in {environment}")
            return True
        except Exception as e:
            logger.error(f"Failed to store calibration: {str(e)}")
            return False
    
    def get_latest_mic_calibration(self) -> Optional[float]:
        """Get latest microphone calibration level"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT ambient_noise_level FROM mic_calibration ORDER BY calibration_id DESC LIMIT 1"
                    )
                    row = cursor.fetchone()
                    return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to get calibration: {str(e)}")
            return None


class MultiVoiceSynthesisEngine:
    """
    Dual-voice synthesis selector for Male/Female offline voices
    Uses local pyttsx3 for text-to-speech without cloud APIs
    """
    
    def __init__(self):
        self.engine = None
        self.available_voices = []
        self.current_voice = "male"
        self.current_voice_id: Optional[str] = None
        self.current_rate = 150
        self.current_volume = 1.0
        self.memory_system = LocalMemorySystem()
        
        self._initialize_tts_engine()
    
    def _infer_voice_gender(self, voice) -> str:
        text = "".join([
            str(getattr(voice, attr, "") or "").lower()
            for attr in ["gender", "name", "id"]
        ])
        if "female" in text or "zira" in text or "anna" in text or "susan" in text:
            return "female"
        if "male" in text or "david" in text or "mark" in text or "paul" in text:
            return "male"
        return "default"
    
    def _initialize_tts_engine(self):
        """Initialize pyttsx3 text-to-speech engine"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Discover available voices
            voices = self.engine.getProperty('voices')
            self.available_voices = [
                {
                    "id": voice.id,
                    "name": getattr(voice, "name", str(voice.id)),
                    "gender": self._infer_voice_gender(voice),
                }
                for voice in voices
            ]
            
            preferred_gender = self.memory_system.get_preference("active_voice_gender", "male")
            self.select_voice(preferred_gender)
            
            logger.info(f"TTS Engine initialized with {len(self.available_voices)} voices")
            logger.debug(f"Available voices: {[v['name'] for v in self.available_voices]}")
        except ImportError:
            logger.warning("pyttsx3 not available; text-to-speech disabled")
            self.engine = None
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def _create_engine(self):
        """Create a fresh pyttsx3 engine instance for each speech call."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            if self.current_voice_id:
                engine.setProperty('voice', self.current_voice_id)
            engine.setProperty('rate', self.current_rate)
            engine.setProperty('volume', self.current_volume)
            return engine
        except Exception as e:
            logger.error(f"Failed to create TTS engine instance: {e}")
            return None
    
    def list_available_voices(self) -> List[Dict]:
        """List all available voice profiles"""
        return self.available_voices
    
    def select_voice(self, voice_type: str = "male"):
        """Select voice type (male/female)"""
        target_voice = next(
            (v for v in self.available_voices if v["gender"] == voice_type.lower()),
            None
        )
        
        if not target_voice and self.available_voices:
            target_voice = self.available_voices[0]
            logger.warning(
                f"Requested voice '{voice_type}' not found, falling back to '{target_voice['name']}'"
            )
            self.current_voice = target_voice["gender"] or "default"
        elif target_voice:
            self.current_voice = voice_type.lower()
        else:
            logger.error("No voices available to select")
            return False
        
        self.current_voice_id = target_voice["id"]
        self.memory_system.set_preference("active_voice_gender", self.current_voice)
        self.memory_system.set_preference("active_voice", self.current_voice)
        logger.info(f"Voice switched to: {target_voice['name']} ({self.current_voice})")
        if self.engine:
            try:
                self.engine.setProperty('voice', self.current_voice_id)
            except Exception:
                pass
        return True
    
    def set_voice_parameters(self, rate: int = 150, volume: float = 1.0):
        """Configure voice pitch, rate, and volume"""
        self.current_rate = rate
        self.current_volume = volume
        if self.engine:
            try:
                self.engine.setProperty('rate', rate)
                self.engine.setProperty('volume', volume)
            except Exception as e:
                logger.error(f"Failed to set voice parameters: {str(e)}")
                return False
        logger.info(f"Voice parameters: rate={rate}, volume={volume}")
        return True
    
    def synthesize_speech(self, text: str, save_to_file: Optional[Path] = None) -> bool:
        """Convert text to speech"""
        engine = self._create_engine()
        if not engine:
            logger.error("TTS engine not available")
            return False
        
        try:
            if save_to_file:
                engine.save_to_file(text, str(save_to_file))
            else:
                engine.say(text)
            engine.runAndWait()
            engine.stop()
            logger.info(f"Speech synthesized: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Speech synthesis failed: {str(e)}")
            try:
                engine.stop()
            except Exception:
                pass
            return False
    
    def speak_adaptive(self, text: str):
        """Speak text with user's preferred call name integrated"""
        user_name = self.memory_system.get_voice_preference()
        adaptive_text = text.replace("[USER_NAME]", user_name)
        return self.synthesize_speech(adaptive_text)


class HandshakeDeleteProtection:
    """
    Deletion confirmation system preventing accidental file/folder destruction
    Voice/text confirmation handshake required before destructive operations
    """
    
    def __init__(self, confirmation_callback: Optional[callable] = None):
        self.confirmation_callback = confirmation_callback
        self.pending_confirmations = {}
    
    def request_deletion_confirmation(self, target_path: Path, operation: str = "delete") -> str:
        """
        Request user confirmation before destructive operation
        Returns confirmation token
        """
        confirmation_id = f"{int(datetime.now().timestamp() * 1000)}"
        
        self.pending_confirmations[confirmation_id] = {
            "target": str(target_path),
            "operation": operation,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
        }
        
        message = f"HANDSHAKE: Confirm {operation} of '{target_path.name}'? Reply 'YES' or 'NO'."
        
        if self.confirmation_callback:
            self.confirmation_callback(message)
        
        logger.warning(f"Deletion handshake initiated: {target_path}")
        return confirmation_id
    
    def confirm_deletion(self, confirmation_id: str, user_response: str) -> bool:
        """Process user confirmation response"""
        if confirmation_id not in self.pending_confirmations:
            logger.error(f"Unknown confirmation ID: {confirmation_id}")
            return False
        
        confirmation = self.pending_confirmations[confirmation_id]
        user_response_upper = user_response.strip().upper()
        
        if user_response_upper in ["YES", "Y", "CONFIRM", "PROCEED"]:
            confirmation["status"] = "CONFIRMED"
            logger.info(f"Deletion confirmed: {confirmation['target']}")
            return True
        else:
            confirmation["status"] = "REJECTED"
            logger.info(f"Deletion rejected: {confirmation['target']}")
            return False
    
    def get_pending_confirmations(self) -> List[Dict]:
        """Get all pending confirmation requests"""
        return list(self.pending_confirmations.values())


class AdaptiveMicrophoneCalibration:
    """
    Adaptive microphone calibration system
    Measures ambient noise and adjusts speech recognition sensitivity
    """
    
    def __init__(self):
        self.memory_system = LocalMemorySystem()
        self.calibration_level = 0.0
        self.is_calibrating = False
    
    def run_ambient_noise_check(self, duration_seconds: int = 3) -> float:
        """
        Perform room acoustic noise baseline measurement
        Returns ambient noise level (0-100 scale)
        """
        try:
            import speech_recognition as sr
            
            self.is_calibrating = True
            recognizer = sr.Recognizer()
            
            with sr.Microphone() as source:
                logger.info(f"Starting {duration_seconds}s ambient noise calibration...")
                recognizer.adjust_for_ambient_noise(source, duration=duration_seconds)
                
                # Estimate noise level
                noise_level = recognizer.energy_threshold
                self.calibration_level = min(100, (noise_level / 4000) * 100)
            
            self.memory_system.store_mic_calibration(self.calibration_level, "standard_room")
            self.is_calibrating = False
            
            logger.info(f"Mic calibration complete: {self.calibration_level:.1f}")
            return self.calibration_level
        
        except ImportError:
            logger.warning("speech_recognition not available; calibration skipped")
            return 0.0
        except Exception as e:
            logger.error(f"Calibration failed: {str(e)}")
            self.is_calibrating = False
            return 0.0
    
    def get_calibration_sensitivity(self) -> float:
        """Get current microphone sensitivity threshold"""
        stored = self.memory_system.get_latest_mic_calibration()
        if stored:
            self.calibration_level = stored
        return self.calibration_level
    
    def apply_calibration_to_recognizer(self, recognizer) -> bool:
        """Apply calibration settings to speech recognizer"""
        try:
            calibration = self.get_calibration_sensitivity()
            # Map calibration level to energy threshold
            recognizer.energy_threshold = (calibration / 100) * 4000
            logger.info(f"Applied calibration: threshold={recognizer.energy_threshold:.0f}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply calibration: {str(e)}")
            return False


# Global instances
_memory_system: Optional[LocalMemorySystem] = None
_voice_engine: Optional[MultiVoiceSynthesisEngine] = None
_delete_protection: Optional[HandshakeDeleteProtection] = None
_mic_calibration: Optional[AdaptiveMicrophoneCalibration] = None


def get_memory_system() -> LocalMemorySystem:
    """Get or create local memory system"""
    global _memory_system
    if _memory_system is None:
        _memory_system = LocalMemorySystem()
    return _memory_system


def get_voice_engine() -> MultiVoiceSynthesisEngine:
    """Get or create multi-voice synthesis engine"""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = MultiVoiceSynthesisEngine()
    return _voice_engine


def get_delete_protection(callback: Optional[callable] = None) -> HandshakeDeleteProtection:
    """Get or create deletion protection system"""
    global _delete_protection
    if _delete_protection is None:
        _delete_protection = HandshakeDeleteProtection(confirmation_callback=callback)
    return _delete_protection


def get_mic_calibration() -> AdaptiveMicrophoneCalibration:
    """Get or create microphone calibration system"""
    global _mic_calibration
    if _mic_calibration is None:
        _mic_calibration = AdaptiveMicrophoneCalibration()
    return _mic_calibration
