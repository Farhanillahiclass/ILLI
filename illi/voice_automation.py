"""
Voice Command Automation for ILLI OS
Process voice commands and execute automated workflows
"""

import logging
from typing import Optional, Dict, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VoiceCommand:
    """Voice command data structure"""
    text: str
    confidence: float = 0.0
    intent: str = "unknown"
    entities: Dict = None


class VoiceCommandProcessor:
    """Process and execute voice commands"""
    
    def __init__(self, automation_engine=None, power_manager=None, voice_engine=None):
        self.automation_engine = automation_engine
        self.power_manager = power_manager
        self.voice_engine = voice_engine
        
        self.command_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default command handlers"""
        self.register_handler("power_control", self._handle_power_command)
        self.register_handler("launch_app", self._handle_launch_app)
        self.register_handler("query", self._handle_query)
        self.register_handler("schedule_task", self._handle_schedule_task)
        self.register_handler("system_info", self._handle_system_info)
        self.register_handler("files", self._handle_file_operations)
    
    def register_handler(self, intent: str, handler: Callable):
        """Register a command handler for an intent"""
        self.command_handlers[intent] = handler
        logger.info(f"Registered handler for intent: {intent}")
    
    def process_command(self, voice_command: VoiceCommand) -> Dict:
        """Process a voice command and execute appropriate action"""
        try:
            # Get the handler for this intent
            handler = self.command_handlers.get(voice_command.intent)
            
            if handler:
                result = handler(voice_command.text)
                return {
                    "status": "success",
                    "intent": voice_command.intent,
                    "command": voice_command.text,
                    "result": result
                }
            else:
                logger.warning(f"No handler for intent: {voice_command.intent}")
                return {
                    "status": "error",
                    "message": f"Unknown command intent: {voice_command.intent}"
                }
        
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _handle_power_command(self, command: str) -> Dict:
        """Handle power control commands"""
        if not self.power_manager:
            return {"error": "Power manager not available"}
        
        command_lower = command.lower()
        
        if "sleep" in command_lower:
            self.power_manager.sleep_system()
            response = "System going to sleep"
        elif "restart" in command_lower:
            self.power_manager.restart_system(delay_seconds=10)
            response = "System will restart in 10 seconds"
        elif "shutdown" in command_lower:
            self.power_manager.shutdown_system(delay_seconds=10)
            response = "System will shutdown in 10 seconds"
        else:
            response = "Power command not recognized"
        
        if self.voice_engine:
            self.voice_engine.synthesize_speech(response)
        
        return {"action": "power_control", "response": response}
    
    def _handle_launch_app(self, command: str) -> Dict:
        """Handle application launch commands"""
        if not self.power_manager:
            return {"error": "Power manager not available"}
        
        # Extract app name from command
        keywords = ["launch", "open", "start", "run"]
        app_name = command
        for keyword in keywords:
            if keyword in command.lower():
                app_name = command.lower().split(keyword)[-1].strip()
                break
        
        if self.power_manager.launch_application(app_name):
            response = f"Launching {app_name}"
        else:
            response = f"Failed to launch {app_name}"
        
        if self.voice_engine:
            self.voice_engine.synthesize_speech(response)
        
        return {"action": "launch_app", "app": app_name, "response": response}
    
    def _handle_query(self, command: str) -> Dict:
        """Handle information query commands"""
        if not self.automation_engine:
            return {"error": "Automation engine not available"}
        
        # Parse the query
        parsed = self.automation_engine.parse_natural_language(command)
        
        response = f"Processing query: {command}"
        
        if self.voice_engine:
            self.voice_engine.synthesize_speech(response)
        
        return {"action": "query", "parsed": parsed, "response": response}
    
    def _handle_schedule_task(self, command: str) -> Dict:
        """Handle task scheduling commands"""
        response = "Task scheduling not yet implemented"
        
        if self.voice_engine:
            self.voice_engine.synthesize_speech(response)
        
        return {"action": "schedule_task", "response": response}
    
    def _handle_system_info(self, command: str) -> Dict:
        """Handle system information queries"""
        try:
            import psutil
            
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            
            response = f"System status: CPU at {cpu} percent, RAM at {ram.percent} percent"
            
            if self.voice_engine:
                self.voice_engine.synthesize_speech(response)
            
            return {
                "action": "system_info",
                "cpu": cpu,
                "ram": ram.percent,
                "response": response
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_file_operations(self, command: str) -> Dict:
        """Handle file operation commands"""
        response = "File operations not yet implemented"
        
        if self.voice_engine:
            self.voice_engine.synthesize_speech(response)
        
        return {"action": "file_operations", "response": response}


class VoiceRecognitionAdapter:
    """Adapter for speech recognition"""
    
    def __init__(self):
        self.recognizer = None
        self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize speech recognizer"""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            logger.info("✅ Speech recognizer initialized")
        except ImportError:
            logger.warning("SpeechRecognition not available")
            self.recognizer = None
    
    def listen_from_microphone(self, timeout: int = 10, phrase_time_limit: int = 5) -> Optional[str]:
        """Listen for voice input and convert to text"""
        if not self.recognizer:
            logger.error("Recognizer not available")
            return None
        
        try:
            import speech_recognition as sr
            
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("🎤 Listening for voice input...")
                
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            # Try Google Speech Recognition first (free)
            try:
                text = self.recognizer.recognize_google(audio)
                logger.info(f"✅ Recognized: {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition error: {e}")
                return None
        
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return None
    
    def listen_from_audio_file(self, file_path: str) -> Optional[str]:
        """Recognize speech from an audio file"""
        if not self.recognizer:
            return None
        
        try:
            import speech_recognition as sr
            
            with sr.AudioFile(file_path) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio)
            logger.info(f"✅ Recognized from file: {text}")
            return text
        
        except Exception as e:
            logger.error(f"Audio file recognition error: {e}")
            return None


class VoiceAutomationOrchestrator:
    """Orchestrate complete voice automation workflow"""
    
    def __init__(self, automation_engine=None, power_manager=None, voice_engine=None):
        self.recognizer = VoiceRecognitionAdapter()
        self.processor = VoiceCommandProcessor(automation_engine, power_manager, voice_engine)
        self.automation_engine = automation_engine
        self.voice_engine = voice_engine
    
    def start_voice_automation_loop(self, continuous: bool = False):
        """Start voice automation loop"""
        import threading
        
        def automation_loop():
            session_active = True
            while session_active:
                # Listen for command
                command_text = self.recognizer.listen_from_microphone()
                
                if not command_text:
                    logger.warning("No speech detected, trying again...")
                    continue
                
                # Parse intent
                if not self.automation_engine:
                    logger.error("Automation engine not available")
                    break
                
                parsed = self.automation_engine.parse_natural_language(command_text)
                
                # Process command
                voice_cmd = VoiceCommand(
                    text=command_text,
                    confidence=parsed.get("confidence", 0),
                    intent=parsed.get("intent", "unknown")
                )
                
                result = self.processor.process_command(voice_cmd)
                logger.info(f"Command result: {result}")
                
                if not continuous:
                    session_active = False
        
        thread = threading.Thread(target=automation_loop, daemon=True)
        thread.start()
        logger.info("Voice automation loop started")
        return thread
