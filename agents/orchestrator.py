"""
Agent Orchestrator
Manages and coordinates multiple AI agents.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent states"""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"


class AgentType(Enum):
    """Types of agents"""
    MASTER = "master"
    CODING = "coding"
    RESEARCH = "research"
    MEMORY = "memory"
    VISION = "vision"
    VOICE = "voice"
    FILE = "file"
    WEB = "web"
    AUTOMATION = "automation"
    DEVOPS = "devops"
    SECURITY = "security"


@dataclass
class AgentTask:
    """A task for an agent"""
    id: str
    agent_type: AgentType
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_type: AgentType, llm, memory):
        self.agent_type = agent_type
        self.llm = llm
        self.memory = memory
        self.state = AgentState.IDLE
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        
    @abstractmethod
    async def process(self, task: AgentTask) -> Any:
        """Process a task"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        pass
    
    async def start(self):
        """Start the agent"""
        self._running = True
        asyncio.create_task(self._task_loop())
        logger.info(f"{self.agent_type.value} agent started")
    
    async def stop(self):
        """Stop the agent"""
        self._running = False
        logger.info(f"{self.agent_type.value} agent stopped")
    
    async def _task_loop(self):
        """Main task processing loop"""
        while self._running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                self.state = AgentState.WORKING
                
                try:
                    result = await self.process(task)
                    task.result = result
                    task.status = "completed"
                except Exception as e:
                    logger.error(f"Error in {self.agent_type.value} agent: {e}")
                    task.error = str(e)
                    task.status = "failed"
                
                self.state = AgentState.IDLE
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task loop: {e}")
    
    async def submit_task(self, task: AgentTask):
        """Submit a task to this agent"""
        await self.task_queue.put(task)


class MasterAgent(BaseAgent):
    """Master agent that coordinates other agents"""
    
    def __init__(self, llm, memory):
        super().__init__(AgentType.MASTER, llm, memory)
        self.sub_agents: Dict[AgentType, BaseAgent] = {}
        
    async def process(self, task: AgentTask) -> Any:
        """Process a task by delegating to appropriate sub-agent"""
        # Analyze task to determine which agent should handle it
        target_agent = await self._determine_agent(task)
        
        if target_agent and target_agent in self.sub_agents:
            return await self.sub_agents[target_agent].process(task)
        else:
            # Handle with master agent
            return await self._handle_directly(task)
    
    async def _determine_agent(self, task: AgentTask) -> Optional[AgentType]:
        """Determine which agent should handle a task"""
        description = task.description.lower()
        
        if any(keyword in description for keyword in ['code', 'program', 'debug', 'fix']):
            return AgentType.CODING
        elif any(keyword in description for keyword in ['search', 'research', 'find', 'look up']):
            return AgentType.RESEARCH
        elif any(keyword in description for keyword in ['remember', 'recall', 'memory']):
            return AgentType.MEMORY
        elif any(keyword in description for keyword in ['see', 'look', 'vision', 'screen']):
            return AgentType.VISION
        elif any(keyword in description for keyword in ['speak', 'say', 'voice', 'talk']):
            return AgentType.VOICE
        elif any(keyword in description for keyword in ['file', 'document', 'folder']):
            return AgentType.FILE
        elif any(keyword in description for keyword in ['web', 'browser', 'internet']):
            return AgentType.WEB
        elif any(keyword in description for keyword in ['automate', 'schedule', 'trigger']):
            return AgentType.AUTOMATION
        elif any(keyword in description for keyword in ['deploy', 'docker', 'server']):
            return AgentType.DEVOPS
        elif any(keyword in description for keyword in ['security', 'permission', 'safe']):
            return AgentType.SECURITY
        
        return None
    
    async def _handle_directly(self, task: AgentTask) -> Any:
        """Handle task directly with LLM"""
        prompt = f"""
You are the master AI agent. Handle this task:
{task.description}

Context: {task.context}
"""
        response = await self.llm.generate(prompt)
        return response
    
    async def get_capabilities(self) -> List[str]:
        """Get master agent capabilities"""
        return [
            "Task coordination",
            "Agent delegation",
            "Complex reasoning",
            "Decision making",
            "System oversight"
        ]
    
    def register_agent(self, agent: BaseAgent):
        """Register a sub-agent"""
        self.sub_agents[agent.agent_type] = agent
        logger.info(f"Registered {agent.agent_type.value} agent")


class CodingAgent(BaseAgent):
    """Agent specialized in coding tasks"""
    
    async def process(self, task: AgentTask) -> Any:
        """Process a coding task"""
        prompt = f"""
You are a coding specialist. Handle this task:
{task.description}

Context: {task.context}

Provide code solutions with explanations.
"""
        response = await self.llm.generate(prompt)
        
        # Store in memory
        await self.memory.add(
            content=f"Coding task: {task.description}\nResult: {response}",
            memory_type=memory.memory_engine.MemoryType.EPISODIC,
            metadata={'agent': 'coding', 'task_id': task.id}
        )
        
        return response
    
    async def get_capabilities(self) -> List[str]:
        """Get coding agent capabilities"""
        return [
            "Code generation",
            "Debugging",
            "Refactoring",
            "Code review",
            "Documentation"
        ]


class ResearchAgent(BaseAgent):
    """Agent specialized in research tasks"""
    
    async def process(self, task: AgentTask) -> Any:
        """Process a research task"""
        prompt = f"""
You are a research specialist. Handle this task:
{task.description}

Context: {task.context}

Provide thorough research findings with sources.
"""
        response = await self.llm.generate(prompt)
        
        await self.memory.add(
            content=f"Research task: {task.description}\nResult: {response}",
            memory_type=memory.memory_engine.MemoryType.EPISODIC,
            metadata={'agent': 'research', 'task_id': task.id}
        )
        
        return response
    
    async def get_capabilities(self) -> List[str]:
        """Get research agent capabilities"""
        return [
            "Information retrieval",
            "Analysis",
            "Synthesis",
            "Fact-checking",
            "Report generation"
        ]


class AgentOrchestrator:
    """
    Main orchestrator that manages all agents.
    """
    
    def __init__(self, llm, memory):
        self.llm = llm
        self.memory = memory
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.active_agent_count = 0
        self._initialized = False
        
    async def initialize(self):
        """Initialize the orchestrator and all agents"""
        logger.info("Initializing Agent Orchestrator...")
        
        # Create master agent
        master = MasterAgent(self.llm, self.memory)
        
        # Create specialized agents
        coding = CodingAgent(AgentType.CODING, self.llm, self.memory)
        research = ResearchAgent(AgentType.RESEARCH, self.llm, self.memory)
        
        # Register agents with master
        master.register_agent(coding)
        master.register_agent(research)
        
        # Store all agents
        self.agents[AgentType.MASTER] = master
        self.agents[AgentType.CODING] = coding
        self.agents[AgentType.RESEARCH] = research
        
        # Start all agents
        for agent in self.agents.values():
            await agent.start()
        
        self.active_agent_count = len(self.agents)
        self._initialized = True
        logger.info(f"Agent Orchestrator initialized with {self.active_agent_count} agents")
    
    async def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user query through the agent system.
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Response dictionary
        """
        # Create task
        task = AgentTask(
            id=f"task_{hash(query)}",
            agent_type=AgentType.MASTER,
            description=query,
            context=context or {}
        )
        
        # Submit to master agent
        master = self.agents[AgentType.MASTER]
        await master.submit_task(task)
        
        # Wait for completion
        while task.status == "pending":
            await asyncio.sleep(0.1)
        
        return {
            'result': task.result,
            'status': task.status,
            'error': task.error
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            agent_type.value: {
                'state': agent.state.value,
                'queue_size': agent.task_queue.qsize()
            }
            for agent_type, agent in self.agents.items()
        }
    
    async def stop(self):
        """Stop all agents"""
        for agent in self.agents.values():
            await agent.stop()
        logger.info("All agents stopped")
