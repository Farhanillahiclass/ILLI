"""
ILLI AI Core Engine
Main engine that orchestrates all AI components.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EngineState(Enum):
    """Engine states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    path: str
    context_size: int = 4096
    gpu_layers: int = -1  # -1 means all
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    quantization: str = "q4_k_m"


@dataclass
class SystemStatus:
    """System status information"""
    state: EngineState = EngineState.STOPPED
    model_loaded: bool = False
    active_agents: int = 0
    memory_usage_mb: float = 0.0
    gpu_usage_percent: float = 0.0
    cpu_usage_percent: float = 0.0
    uptime_seconds: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_error: Optional[str] = None


class AIEngine:
    """
    Main AI Engine that coordinates all components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/engine_config.json"
        self.state = EngineState.STOPPED
        self.model_config: Optional[ModelConfig] = None
        self.model = None
        self.status = SystemStatus()
        self._components: Dict[str, Any] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        
    async def initialize(self):
        """Initialize the engine and all components"""
        logger.info("Initializing ILLI AI Engine...")
        self.state = EngineState.STARTING
        
        try:
            # Load configuration
            await self._load_config()
            
            # Initialize components
            await self._initialize_components()
            
            self.state = EngineState.RUNNING
            self._running = True
            logger.info("ILLI AI Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize engine: {e}")
            self.state = EngineState.ERROR
            self.status.last_error = str(e)
            raise
    
    async def _load_config(self):
        """Load engine configuration"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.model_config = ModelConfig(**config.get('model', {}))
        else:
            # Default configuration
            self.model_config = ModelConfig(
                name="llama2",
                path="models/llama2-7b.gguf",
                context_size=4096
            )
            logger.info("Using default model configuration")
    
    async def _initialize_components(self):
        """Initialize all engine components"""
        # These will be implemented as separate modules
        from core.llm_interface import LLMInterface
        from memory.memory_engine import MemoryEngine
        from agents.orchestrator import AgentOrchestrator
        
        # Initialize LLM interface
        self._components['llm'] = LLMInterface(self.model_config)
        await self._components['llm'].initialize()
        
        # Initialize memory engine
        self._components['memory'] = MemoryEngine()
        await self._components['memory'].initialize()
        
        # Initialize agent orchestrator
        self._components['agents'] = AgentOrchestrator(
            llm=self._components['llm'],
            memory=self._components['memory']
        )
        await self._components['agents'].initialize()
        
        logger.info("All components initialized")
    
    async def start(self):
        """Start the engine"""
        if self.state == EngineState.RUNNING:
            logger.warning("Engine already running")
            return
        
        await self.initialize()
        
        # Start background tasks
        asyncio.create_task(self._event_loop())
        asyncio.create_task(self._status_update_loop())
        
        logger.info("ILLI AI Engine started")
    
    async def stop(self):
        """Stop the engine"""
        logger.info("Stopping ILLI AI Engine...")
        self.state = EngineState.STOPPING
        self._running = False
        
        # Stop all components
        for component in self._components.values():
            if hasattr(component, 'stop'):
                await component.stop()
        
        self.state = EngineState.STOPPED
        logger.info("ILLI AI Engine stopped")
    
    async def _event_loop(self):
        """Main event processing loop"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _process_event(self, event: Dict[str, Any]):
        """Process a single event"""
        event_type = event.get('type')
        
        if event_type == 'query':
            await self._handle_query(event)
        elif event_type == 'command':
            await self._handle_command(event)
        elif event_type == 'status':
            await self._handle_status_request(event)
    
    async def _handle_query(self, event: Dict[str, Any]):
        """Handle a query event"""
        query = event.get('query', '')
        context = event.get('context', {})
        
        # Route to appropriate agent
        orchestrator = self._components.get('agents')
        if orchestrator:
            response = await orchestrator.process_query(query, context)
            # Send response back
            if 'callback' in event and event['callback']:
                callback = event['callback']
                if asyncio.iscoroutinefunction(callback):
                    await callback(response)
                else:
                    callback(response)
    
    async def _handle_command(self, event: Dict[str, Any]):
        """Handle a command event"""
        command = event.get('command', '')
        params = event.get('params', {})
        
        # Execute command
        logger.info(f"Executing command: {command}")
        
        # Handle start/stop commands
        if command == 'start':
            if self.state != EngineState.RUNNING:
                await self.start()
        elif command == 'stop':
            if self.state == EngineState.RUNNING:
                await self.stop()
        
        # Send response back
        if 'callback' in event and event['callback']:
            callback = event['callback']
            if asyncio.iscoroutinefunction(callback):
                await callback({"success": True})
            else:
                callback({"success": True})
    
    async def _handle_status_request(self, event: Dict[str, Any]):
        """Handle status request"""
        if 'callback' in event and event['callback']:
            callback = event['callback']
            if asyncio.iscoroutinefunction(callback):
                await callback(self.status)
            else:
                callback(self.status)
    
    async def _status_update_loop(self):
        """Update system status periodically"""
        import psutil
        
        while self._running:
            try:
                # Update system stats
                self.status.cpu_usage_percent = psutil.cpu_percent()
                self.status.memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
                
                # Update component stats
                if 'agents' in self._components:
                    self.status.active_agents = self._components['agents'].active_agent_count
                
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
                await asyncio.sleep(5)
    
    async def query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Submit a query to the engine.
        
        Args:
            query: The query text
            context: Additional context for the query
            
        Returns:
            Response dictionary
        """
        response_future = asyncio.Future()
        
        await self._event_queue.put({
            'type': 'query',
            'query': query,
            'context': context or {},
            'callback': response_future.set_result
        })
        
        return await response_future
    
    async def command(self, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a command.
        
        Args:
            command: The command to execute
            params: Command parameters
            
        Returns:
            Result dictionary
        """
        result_future = asyncio.Future()
        
        await self._event_queue.put({
            'type': 'command',
            'command': command,
            'params': params or {},
            'callback': result_future.set_result
        })
        
        return await result_future
    
    def get_status(self) -> SystemStatus:
        """Get current system status"""
        return self.status


# Singleton instance
_engine_instance: Optional[AIEngine] = None


def get_engine() -> AIEngine:
    """Get the singleton engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngine()
    return _engine_instance
