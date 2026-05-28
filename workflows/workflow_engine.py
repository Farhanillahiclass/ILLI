"""
Workflow Engine
Manages automation workflows and task orchestration.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of workflow nodes"""
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    DELAY = "delay"
    LOOP = "loop"
    PARALLEL = "parallel"
    MERGE = "merge"
    END = "end"


class NodeStatus(Enum):
    """Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """A single node in a workflow"""
    id: str
    type: NodeType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """Execution state of a workflow"""
    workflow_id: str
    execution_id: str
    status: str = "running"
    started_at: datetime = None
    completed_at: Optional[datetime] = None
    node_states: Dict[str, NodeStatus] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Workflow:
    """A workflow definition"""
    
    def __init__(self, workflow_id: str, name: str):
        self.id = workflow_id
        self.name = name
        self.nodes: List[WorkflowNode] = []
        self.edges: List[Dict[str, str]] = []
        self.variables: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def add_node(self, node: WorkflowNode):
        """Add a node to the workflow"""
        self.nodes.append(node)
        self.updated_at = datetime.now()
    
    def add_edge(self, from_node: str, to_node: str):
        """Add an edge between nodes"""
        self.edges.append({"from": from_node, "to": to_node})
        self.updated_at = datetime.now()
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "name": n.name,
                    "config": n.config,
                    "position": n.position,
                    "inputs": n.inputs,
                    "outputs": n.outputs
                }
                for n in self.nodes
            ],
            "edges": self.edges,
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Create workflow from dictionary"""
        workflow = cls(data["id"], data["name"])
        
        for node_data in data["nodes"]:
            node = WorkflowNode(
                id=node_data["id"],
                type=NodeType(node_data["type"]),
                name=node_data["name"],
                config=node_data.get("config", {}),
                position=node_data.get("position", {}),
                inputs=node_data.get("inputs", []),
                outputs=node_data.get("outputs", [])
            )
            workflow.add_node(node)
        
        workflow.edges = data.get("edges", [])
        workflow.variables = data.get("variables", {})
        workflow.created_at = datetime.fromisoformat(data["created_at"])
        workflow.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return workflow


class WorkflowEngine:
    """
    Main workflow engine for executing automation workflows.
    """
    
    def __init__(self, storage_dir: str = "data/workflows"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._workflows: Dict[str, Workflow] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._action_handlers: Dict[str, Callable] = {}
        self._running = False
        self._initialized = False
        
    async def initialize(self):
        """Initialize the workflow engine"""
        logger.info("Initializing Workflow Engine...")
        
        # Load existing workflows
        await self._load_workflows()
        
        # Register default action handlers
        await self._register_default_handlers()
        
        self._running = True
        self._initialized = True
        logger.info("Workflow Engine initialized")
    
    async def _load_workflows(self):
        """Load workflows from storage"""
        for workflow_file in self.storage_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    data = json.load(f)
                    workflow = Workflow.from_dict(data)
                    self._workflows[workflow.id] = workflow
            except Exception as e:
                logger.error(f"Error loading workflow {workflow_file}: {e}")
        
        logger.info(f"Loaded {len(self._workflows)} workflows")
    
    async def _register_default_handlers(self):
        """Register default action handlers"""
        self._action_handlers = {
            "log": self._handle_log,
            "delay": self._handle_delay,
            "http_request": self._handle_http_request,
            "file_write": self._handle_file_write,
            "file_read": self._handle_file_read,
            "execute_command": self._handle_execute_command
        }
    
    async def create_workflow(self, name: str) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            
        Returns:
            Created workflow
        """
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(workflow_id, name)
        self._workflows[workflow_id] = workflow
        
        await self._save_workflow(workflow)
        logger.info(f"Created workflow: {name} ({workflow_id})")
        
        return workflow
    
    async def save_workflow(self, workflow: Workflow):
        """
        Save a workflow.
        
        Args:
            workflow: Workflow to save
        """
        workflow.updated_at = datetime.now()
        await self._save_workflow(workflow)
        logger.info(f"Saved workflow: {workflow.name}")
    
    async def _save_workflow(self, workflow: Workflow):
        """Save workflow to file"""
        workflow_file = self.storage_dir / f"{workflow.id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow.to_dict(), f, indent=2)
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted successfully
        """
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            
            workflow_file = self.storage_dir / f"{workflow_id}.json"
            if workflow_file.exists():
                workflow_file.unlink()
            
            logger.info(f"Deleted workflow: {workflow_id}")
            return True
        
        return False
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        return self._workflows.get(workflow_id)
    
    async def list_workflows(self) -> List[Workflow]:
        """List all workflows"""
        return list(self._workflows.values())
    
    async def execute_workflow(self, workflow_id: str, 
                              variables: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow ID
            variables: Initial variables
            
        Returns:
            Workflow execution
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            execution_id=execution_id,
            started_at=datetime.now()
        )
        
        # Merge variables
        if variables:
            workflow.variables.update(variables)
        
        self._executions[execution_id] = execution
        
        # Execute workflow
        asyncio.create_task(self._execute_workflow_async(workflow, execution))
        
        return execution
    
    async def _execute_workflow_async(self, workflow: Workflow, execution: WorkflowExecution):
        """Execute workflow asynchronously"""
        try:
            # Find trigger nodes
            trigger_nodes = [n for n in workflow.nodes if n.type == NodeType.TRIGGER]
            
            if not trigger_nodes:
                # Start from first node
                if workflow.nodes:
                    await self._execute_node(workflow.nodes[0], workflow, execution)
            else:
                # Execute all trigger nodes
                for trigger in trigger_nodes:
                    await self._execute_node(trigger, workflow, execution)
            
            execution.status = "completed"
            execution.completed_at = datetime.now()
            logger.info(f"Workflow execution completed: {execution.execution_id}")
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.now()
            logger.error(f"Workflow execution failed: {execution.execution_id} - {e}")
    
    async def _execute_node(self, node: WorkflowNode, workflow: Workflow, 
                           execution: WorkflowExecution):
        """Execute a single node"""
        execution.node_states[node.id] = NodeStatus.RUNNING
        
        try:
            result = await self._execute_node_logic(node, workflow, execution)
            execution.results[node.id] = result
            execution.node_states[node.id] = NodeStatus.COMPLETED
            
            # Execute connected nodes
            for edge in workflow.edges:
                if edge["from"] == node.id:
                    next_node = workflow.get_node(edge["to"])
                    if next_node:
                        await self._execute_node(next_node, workflow, execution)
                        
        except Exception as e:
            execution.node_states[node.id] = NodeStatus.FAILED
            execution.error = str(e)
            logger.error(f"Node execution failed: {node.id} - {e}")
    
    async def _execute_node_logic(self, node: WorkflowNode, workflow: Workflow, 
                                 execution: WorkflowExecution) -> Any:
        """Execute the logic of a node"""
        node_type = node.type
        config = node.config
        
        if node_type == NodeType.TRIGGER:
            return {"triggered": True, "timestamp": datetime.now().isoformat()}
        
        elif node_type == NodeType.ACTION:
            action_type = config.get("action")
            handler = self._action_handlers.get(action_type)
            if handler:
                return await handler(config, workflow.variables)
            else:
                raise ValueError(f"Unknown action: {action_type}")
        
        elif node_type == NodeType.CONDITION:
            condition = config.get("condition")
            # Simple condition evaluation
            return eval(condition, {}, workflow.variables)
        
        elif node_type == NodeType.DELAY:
            delay_seconds = config.get("seconds", 1)
            await asyncio.sleep(delay_seconds)
            return {"delayed": delay_seconds}
        
        elif node_type == NodeType.LOOP:
            # Loop logic
            iterations = config.get("iterations", 1)
            results = []
            for i in range(iterations):
                # Execute connected nodes for each iteration
                pass
            return {"iterations": iterations, "results": results}
        
        elif node_type == NodeType.PARALLEL:
            # Execute connected nodes in parallel
            tasks = []
            for edge in workflow.edges:
                if edge["from"] == node.id:
                    next_node = workflow.get_node(edge["to"])
                    if next_node:
                        tasks.append(self._execute_node(next_node, workflow, execution))
            await asyncio.gather(*tasks)
            return {"parallel": True}
        
        elif node_type == NodeType.END:
            execution.status = "completed"
            execution.completed_at = datetime.now()
            return {"ended": True}
        
        return {}
    
    # Default action handlers
    async def _handle_log(self, config: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Handle log action"""
        message = config.get("message", "").format(**variables)
        logger.info(f"[Workflow] {message}")
        return {"logged": message}
    
    async def _handle_delay(self, config: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delay action"""
        delay = config.get("seconds", 1)
        await asyncio.sleep(delay)
        return {"delayed": delay}
    
    async def _handle_http_request(self, config: Dict[str, Any], 
                                   variables: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HTTP request action"""
        import aiohttp
        
        url = config.get("url", "").format(**variables)
        method = config.get("method", "GET").upper()
        
        async with aiohttp.ClientSession() as session:
            async with getattr(session, method.lower())(url) as resp:
                data = await resp.text()
                return {"status": resp.status, "data": data}
    
    async def _handle_file_write(self, config: Dict[str, Any], 
                                 variables: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file write action"""
        path = config.get("path", "").format(**variables)
        content = config.get("content", "").format(**variables)
        
        with open(path, 'w') as f:
            f.write(content)
        
        return {"written": path}
    
    async def _handle_file_read(self, config: Dict[str, Any], 
                                variables: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file read action"""
        path = config.get("path", "").format(**variables)
        
        with open(path, 'r') as f:
            content = f.read()
        
        return {"content": content}
    
    async def _handle_execute_command(self, config: Dict[str, Any], 
                                     variables: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute command action"""
        command = config.get("command", "").format(**variables)
        
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def register_action_handler(self, action_type: str, handler: Callable):
        """
        Register a custom action handler.
        
        Args:
            action_type: Type of action
            handler: Handler function
        """
        self._action_handlers[action_type] = handler
        logger.info(f"Registered action handler: {action_type}")
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get an execution by ID"""
        return self._executions.get(execution_id)
    
    async def get_workflow_executions(self, workflow_id: str) -> List[WorkflowExecution]:
        """Get all executions for a workflow"""
        return [
            exec for exec in self._executions.values()
            if exec.workflow_id == workflow_id
        ]
    
    async def stop(self):
        """Stop the workflow engine"""
        self._running = False
        logger.info("Workflow Engine stopped")


class WorkflowVisualizer:
    """
    Provides visualization data for workflows.
    """
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow_engine = workflow_engine
    
    async def get_workflow_graph(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow graph data for visualization.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Graph data
        """
        workflow = await self.workflow_engine.get_workflow(workflow_id)
        if not workflow:
            return {}
        
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "name": n.name,
                    "position": n.position,
                    "data": n.config
                }
                for n in workflow.nodes
            ],
            "edges": workflow.edges
        }
    
    async def get_execution_timeline(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Get execution timeline for visualization.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Timeline data
        """
        execution = await self.workflow_engine.get_execution(execution_id)
        if not execution:
            return []
        
        timeline = []
        for node_id, status in execution.node_states.items():
            timeline.append({
                "node_id": node_id,
                "status": status.value,
                "result": execution.results.get(node_id)
            })
        
        return timeline
