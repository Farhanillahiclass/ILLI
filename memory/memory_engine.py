"""
Memory Engine
Manages different types of memory: short-term, long-term, semantic, episodic.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    WORKING = "working"


@dataclass
class MemoryItem:
    """A single memory item"""
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    importance: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class MemoryEngine:
    """
    Main memory engine that manages all memory types.
    """
    
    def __init__(self, data_dir: str = "data/memory"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory stores
        self.short_term: List[MemoryItem] = []
        self.long_term: List[MemoryItem] = []
        self.semantic_memory: Dict[str, List[float]] = {}  # For vector search
        self.episodic_memory: List[MemoryItem] = []
        self.working_memory: Dict[str, Any] = {}
        
        # Limits
        self.short_term_limit = 100
        self.working_memory_limit = 50
        
        self._initialized = False
        
    async def initialize(self):
        """Initialize the memory engine"""
        logger.info("Initializing Memory Engine...")
        
        # Load existing memories from disk
        await self._load_memories()
        
        self._initialized = True
        logger.info("Memory Engine initialized")
    
    async def _load_memories(self):
        """Load memories from disk"""
        # Load long-term memory
        lt_file = self.data_dir / "long_term.json"
        if lt_file.exists():
            with open(lt_file, 'r') as f:
                data = json.load(f)
                self.long_term = [
                    MemoryItem(
                        id=item['id'],
                        content=item['content'],
                        memory_type=MemoryType(item['memory_type']),
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        metadata=item.get('metadata', {}),
                        embeddings=item.get('embeddings'),
                        importance=item.get('importance', 0.5),
                        access_count=item.get('access_count', 0),
                        last_accessed=datetime.fromisoformat(item['last_accessed']) if item.get('last_accessed') else None
                    )
                    for item in data
                ]
        
        # Load episodic memory
        ep_file = self.data_dir / "episodic.json"
        if ep_file.exists():
            with open(ep_file, 'r') as f:
                data = json.load(f)
                self.episodic_memory = [
                    MemoryItem(
                        id=item['id'],
                        content=item['content'],
                        memory_type=MemoryType.EPISODIC,
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        metadata=item.get('metadata', {}),
                        importance=item.get('importance', 0.5)
                    )
                    for item in data
                ]
        
        logger.info(f"Loaded {len(self.long_term)} long-term and {len(self.episodic_memory)} episodic memories")
    
    async def save_memories(self):
        """Save memories to disk"""
        # Save long-term memory
        lt_file = self.data_dir / "long_term.json"
        with open(lt_file, 'w') as f:
            json.dump([
                {
                    'id': item.id,
                    'content': item.content,
                    'memory_type': item.memory_type.value,
                    'timestamp': item.timestamp.isoformat(),
                    'metadata': item.metadata,
                    'embeddings': item.embeddings,
                    'importance': item.importance,
                    'access_count': item.access_count,
                    'last_accessed': item.last_accessed.isoformat() if item.last_accessed else None
                }
                for item in self.long_term
            ], f, indent=2)
        
        # Save episodic memory
        ep_file = self.data_dir / "episodic.json"
        with open(ep_file, 'w') as f:
            json.dump([
                {
                    'id': item.id,
                    'content': item.content,
                    'timestamp': item.timestamp.isoformat(),
                    'metadata': item.metadata,
                    'importance': item.importance
                }
                for item in self.episodic_memory
            ], f, indent=2)
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for a memory item"""
        hash_input = f"{content}_{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    async def add(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> str:
        """
        Add a memory item.
        
        Args:
            content: The content to remember
            memory_type: Type of memory
            metadata: Additional metadata
            importance: Importance score (0-1)
            
        Returns:
            Memory item ID
        """
        if not self._initialized:
            await self.initialize()
        
        memory_item = MemoryItem(
            id=self._generate_id(content),
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            metadata=metadata or {},
            importance=importance,
            last_accessed=datetime.now()
        )
        
        # Add to appropriate store
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term.append(memory_item)
            # Enforce limit
            if len(self.short_term) > self.short_term_limit:
                self.short_term.pop(0)
        elif memory_type == MemoryType.LONG_TERM:
            self.long_term.append(memory_item)
            # Generate embeddings for semantic search
            await self._generate_embeddings(memory_item)
        elif memory_type == MemoryType.EPISODIC:
            self.episodic_memory.append(memory_item)
        elif memory_type == MemoryType.WORKING:
            if len(self.working_memory) >= self.working_memory_limit:
                # Remove oldest
                oldest_key = min(self.working_memory.keys())
                del self.working_memory[oldest_key]
            self.working_memory[memory_item.id] = memory_item
        
        logger.debug(f"Added {memory_type.value} memory: {content[:50]}...")
        return memory_item.id
    
    async def _generate_embeddings(self, memory_item: MemoryItem):
        """Generate embeddings for semantic search"""
        # This would use a sentence transformer model
        # For now, use a simple hash-based approach
        import numpy as np
        content_hash = hash(memory_item.content)
        memory_item.embeddings = [float((content_hash >> i) & 0xFF) / 255.0 for i in range(128)]
    
    async def retrieve(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[MemoryItem]:
        """
        Retrieve memories based on a query.
        
        Args:
            query: Search query
            memory_type: Type of memory to search
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching memory items
        """
        if not self._initialized:
            await self.initialize()
        
        # Determine which memory store to search
        if memory_type == MemoryType.SHORT_TERM:
            memories = self.short_term
        elif memory_type == MemoryType.LONG_TERM:
            memories = self.long_term
        elif memory_type == MemoryType.EPISODIC:
            memories = self.episodic_memory
        else:
            # Search all
            memories = self.short_term + self.long_term + self.episodic_memory
        
        # Simple keyword matching for now
        # In production, use semantic search with embeddings
        results = []
        query_lower = query.lower()
        
        for memory in memories:
            if query_lower in memory.content.lower():
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                results.append(memory)
        
        # Sort by importance and access count
        results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
        
        return results[:limit]
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID"""
        # Search all memory stores
        all_memories = self.short_term + self.long_term + self.episodic_memory
        for memory in all_memories:
            if memory.id == memory_id:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                return memory
        return None
    
    async def update(self, memory_id: str, content: Optional[str] = None, metadata: Optional[Dict] = None):
        """Update a memory item"""
        memory = await self.get(memory_id)
        if memory:
            if content:
                memory.content = content
            if metadata:
                memory.metadata.update(metadata)
            logger.debug(f"Updated memory {memory_id}")
    
    async def delete(self, memory_id: str):
        """Delete a memory item"""
        # Remove from all stores
        self.short_term = [m for m in self.short_term if m.id != memory_id]
        self.long_term = [m for m in self.long_term if m.id != memory_id]
        self.episodic_memory = [m for m in self.episodic_memory if m.id != memory_id]
        if memory_id in self.working_memory:
            del self.working_memory[memory_id]
        logger.debug(f"Deleted memory {memory_id}")
    
    async def clear_short_term(self):
        """Clear short-term memory"""
        self.short_term.clear()
        logger.info("Short-term memory cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'short_term_count': len(self.short_term),
            'long_term_count': len(self.long_term),
            'episodic_count': len(self.episodic_memory),
            'working_memory_count': len(self.working_memory),
            'total_memories': len(self.short_term) + len(self.long_term) + len(self.episodic_memory)
        }
    
    async def cleanup_old_memories(self, days: int = 30):
        """Remove memories older than specified days"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        # Clean long-term memory
        self.long_term = [m for m in self.long_term if m.timestamp > cutoff or m.importance > 0.8]
        
        # Clean episodic memory
        self.episodic_memory = [m for m in self.episodic_memory if m.timestamp > cutoff or m.importance > 0.8]
        
        await self.save_memories()
        logger.info(f"Cleaned up memories older than {days} days")
