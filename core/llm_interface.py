"""
LLM Interface
Handles communication with local LLM models (Ollama, llama.cpp, etc.)
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    stop_sequences: Optional[List[str]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class LLMInterface:
    """
    Interface for interacting with local LLM models.
    Supports multiple backends: Ollama, llama.cpp, etc.
    """
    
    def __init__(self, model_config):
        from core.engine import ModelConfig
        self.model_config: ModelConfig = model_config
        self.backend = "ollama"  # Default backend
        self.model = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the LLM backend"""
        logger.info(f"Initializing LLM interface with model: {self.model_config.name}")
        
        # Try to detect available backends
        if await self._check_ollama():
            self.backend = "ollama"
            await self._init_ollama()
        elif await self._check_llama_cpp():
            self.backend = "llama_cpp"
            await self._init_llama_cpp()
        else:
            logger.warning("No LLM backend detected, using mock mode")
            self.backend = "mock"
        
        self._initialized = True
        logger.info(f"LLM interface initialized with backend: {self.backend}")
    
    async def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:11434/api/tags', timeout=2) as resp:
                    return resp.status == 200
        except:
            return False
    
    async def _init_ollama(self):
        """Initialize Ollama backend"""
        import aiohttp
        self.ollama_session = aiohttp.ClientSession()
        
        # Check if model is available
        try:
            async with self.ollama_session.get('http://localhost:11434/api/tags') as resp:
                data = await resp.json()
                models = [m['name'] for m in data.get('models', [])]
                
                if self.model_config.name not in models:
                    logger.info(f"Model {self.model_config.name} not found, pulling...")
                    await self._pull_ollama_model()
        except Exception as e:
            logger.error(f"Error checking Ollama models: {e}")
    
    async def _pull_ollama_model(self):
        """Pull a model from Ollama"""
        import aiohttp
        
        logger.info(f"Pulling model {self.model_config.name}...")
        try:
            async with self.ollama_session.post(
                'http://localhost:11434/api/pull',
                json={'name': self.model_config.name}
            ) as resp:
                # Stream the response
                async for line in resp.content:
                    logger.debug(line.decode())
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
    
    async def _check_llama_cpp(self) -> bool:
        """Check if llama.cpp is available"""
        try:
            from llama_cpp import Llama
            # Check if model file exists
            model_path = Path(self.model_config.path)
            return model_path.exists()
        except:
            return False
    
    async def _init_llama_cpp(self):
        """Initialize llama.cpp backend"""
        try:
            from llama_cpp import Llama
            self.model = Llama(
                model_path=self.model_config.path,
                n_ctx=self.model_config.context_size,
                n_gpu_layers=self.model_config.gpu_layers,
                verbose=False
            )
            logger.info("llama.cpp backend initialized")
        except Exception as e:
            logger.error(f"Error initializing llama.cpp: {e}")
            self.backend = "mock"
    
    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text from the model.
        
        Args:
            prompt: Input prompt
            config: Generation configuration
            stream: Whether to stream the response
            
        Returns:
            Generated text
        """
        if not self._initialized:
            await self.initialize()
        
        config = config or GenerationConfig()
        
        if self.backend == "ollama":
            return await self._generate_ollama(prompt, config, stream)
        elif self.backend == "llama_cpp":
            return await self._generate_llama_cpp(prompt, config, stream)
        else:
            return await self._generate_mock(prompt, config)
    
    async def _generate_ollama(
        self,
        prompt: str,
        config: GenerationConfig,
        stream: bool
    ) -> str:
        """Generate using Ollama"""
        import aiohttp
        
        payload = {
            'model': self.model_config.name,
            'prompt': prompt,
            'stream': stream,
            'options': {
                'temperature': config.temperature,
                'top_p': config.top_p,
                'num_predict': config.max_tokens
            }
        }
        
        if config.stop_sequences:
            payload['options']['stop'] = config.stop_sequences
        
        try:
            async with self.ollama_session.post(
                'http://localhost:11434/api/generate',
                json=payload
            ) as resp:
                if stream:
                    # Handle streaming
                    full_response = ""
                    async for line in resp.content:
                        data = json.loads(line.decode())
                        if 'response' in data:
                            full_response += data['response']
                    return full_response
                else:
                    data = await resp.json()
                    return data.get('response', '')
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Error: {str(e)}"
    
    async def _generate_llama_cpp(
        self,
        prompt: str,
        config: GenerationConfig,
        stream: bool
    ) -> str:
        """Generate using llama.cpp"""
        try:
            output = self.model(
                prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                stop=config.stop_sequences,
                echo=False
            )
            return output['choices'][0]['text']
        except Exception as e:
            logger.error(f"llama.cpp generation error: {e}")
            return f"Error: {str(e)}"
    
    async def _generate_mock(self, prompt: str, config: GenerationConfig) -> str:
        """Mock generation for testing"""
        return f"[MOCK RESPONSE] This is a simulated response to: {prompt[:50]}..."
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        config: Optional[GenerationConfig] = None
    ) -> str:
        """
        Generate a chat response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            config: Generation configuration
            
        Returns:
            Generated response
        """
        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages)
        return await self.generate(prompt, config)
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to prompt format"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.upper()}: {content}")
        prompt_parts.append("ASSISTANT:")
        return "\n".join(prompt_parts)
    
    async def close(self):
        """Close the LLM interface"""
        if self.backend == "ollama" and hasattr(self, 'ollama_session'):
            await self.ollama_session.close()
        logger.info("LLM interface closed")
