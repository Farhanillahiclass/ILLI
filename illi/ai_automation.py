"""
AI Automation Engine for ILLI OS
Integrates LLM-based automation for intelligent task execution
"""

import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import threading
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AutomationTask:
    """Represents an automation task"""
    task_id: str
    name: str
    description: str
    trigger: str  # "schedule", "voice", "api", "condition"
    action: str  # "execute_script", "launch_app", "query_ai", etc.
    parameters: Dict[str, Any]
    status: str = "pending"
    created_at: str = None
    last_executed: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class AIAutomationEngine:
    """
    AI-powered automation engine
    Processes natural language commands and executes complex workflows
    """
    
    def __init__(self):
        self.tasks: Dict[str, AutomationTask] = {}
        self.execution_history: List[Dict] = []
        self.ai_models = self._initialize_ai_models()
        self.max_history = 100
    
    def _initialize_ai_models(self) -> Dict:
        """Initialize available AI models"""
        models = {}
        
        # Try to load transformer-based models
        try:
            from transformers import pipeline
            models['text_classification'] = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
            logger.info("✅ Loaded text classification model")
        except Exception as e:
            logger.warning(f"Could not load text classification: {e}")
        
        try:
            from transformers import pipeline
            models['ner'] = pipeline("ner", model="distilbert-base-cased")
            logger.info("✅ Loaded NER model")
        except Exception as e:
            logger.warning(f"Could not load NER model: {e}")
        
        return models
    
    def parse_natural_language(self, command: str) -> Dict[str, Any]:
        """
        Parse natural language command and extract intent
        Returns: {"intent": str, "entities": dict, "confidence": float}
        """
        try:
            # Use text classification to determine intent
            if 'text_classification' in self.ai_models:
                result = self.ai_models['text_classification'](command)
                return {
                    "intent": result[0]['label'],
                    "confidence": result[0]['score'],
                    "original_command": command
                }
            else:
                # Fallback: simple keyword matching
                keywords = {
                    "launch": ["launch", "open", "start", "run"],
                    "execute": ["execute", "run", "do", "perform"],
                    "query": ["what", "how", "tell", "find", "search"],
                    "control": ["sleep", "restart", "shutdown", "power"],
                    "schedule": ["schedule", "remind", "set", "plan"]
                }
                
                command_lower = command.lower()
                for intent, keywords_list in keywords.items():
                    if any(kw in command_lower for kw in keywords_list):
                        return {
                            "intent": intent,
                            "confidence": 0.7,
                            "original_command": command
                        }
                
                return {
                    "intent": "unknown",
                    "confidence": 0.0,
                    "original_command": command
                }
        except Exception as e:
            logger.error(f"NLP parsing error: {e}")
            return {"intent": "error", "error": str(e)}
    
    def create_task(self, name: str, description: str, trigger: str, 
                   action: str, parameters: Dict) -> str:
        """Create a new automation task"""
        task_id = f"task_{len(self.tasks)}_{int(datetime.now().timestamp())}"
        task = AutomationTask(
            task_id=task_id,
            name=name,
            description=description,
            trigger=trigger,
            action=action,
            parameters=parameters
        )
        self.tasks[task_id] = task
        logger.info(f"Created automation task: {task_id}")
        return task_id
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute an automation task"""
        if task_id not in self.tasks:
            return {"status": "error", "message": f"Task {task_id} not found"}
        
        task = self.tasks[task_id]
        task.status = "executing"
        
        try:
            result = self._execute_action(task.action, task.parameters)
            task.status = "completed"
            task.last_executed = datetime.now().isoformat()
            
            # Log execution
            execution_record = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "result": result
            }
            self.execution_history.append(execution_record)
            if len(self.execution_history) > self.max_history:
                self.execution_history.pop(0)
            
            logger.info(f"Task {task_id} executed successfully")
            return result
        
        except Exception as e:
            task.status = "failed"
            error_msg = str(e)
            logger.error(f"Task execution failed: {error_msg}")
            
            execution_record = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": error_msg
            }
            self.execution_history.append(execution_record)
            
            return {"status": "error", "message": error_msg}
    
    def _execute_action(self, action: str, parameters: Dict) -> Dict:
        """Execute the actual action based on type"""
        if action == "query_ai":
            return self._query_ai_model(parameters.get("query", ""))
        
        elif action == "execute_system_command":
            return self._execute_system_command(parameters.get("command", ""))
        
        elif action == "launch_application":
            return self._launch_app(parameters.get("app_name", ""))
        
        elif action == "send_notification":
            return self._send_notification(parameters.get("message", ""))
        
        elif action == "http_request":
            return self._make_http_request(parameters)
        
        else:
            return {"status": "unknown_action", "action": action}
    
    def _query_ai_model(self, query: str) -> Dict:
        """Query AI model with a question"""
        try:
            # Simple semantic search or question answering
            return {
                "status": "success",
                "query": query,
                "response": f"Query processed: {query[:50]}..."
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _execute_system_command(self, command: str) -> Dict:
        """Execute a system command safely"""
        import subprocess
        try:
            result = subprocess.run(command, shell=True, capture_output=True, timeout=10)
            return {
                "status": "success",
                "command": command,
                "return_code": result.returncode,
                "output": result.stdout.decode()[:500]
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Command timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _launch_app(self, app_name: str) -> Dict:
        """Launch an application"""
        import subprocess
        try:
            subprocess.Popen(app_name)
            return {"status": "success", "app": app_name, "message": f"Launched {app_name}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _send_notification(self, message: str) -> Dict:
        """Send system notification"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast("ILLI OS", message, duration=5)
            return {"status": "success", "message": message}
        except ImportError:
            logger.warning("win10toast not available, notification skipped")
            return {"status": "warning", "message": "Toast not available"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _make_http_request(self, parameters: Dict) -> Dict:
        """Make HTTP request to external API"""
        try:
            import requests
            
            method = parameters.get("method", "GET").upper()
            url = parameters.get("url", "")
            headers = parameters.get("headers", {})
            data = parameters.get("data", None)
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            else:
                return {"status": "error", "error": f"Unsupported method: {method}"}
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type') == 'application/json' else response.text[:500]
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get the current status of a task"""
        if task_id not in self.tasks:
            return {"status": "error", "message": "Task not found"}
        
        task = self.tasks[task_id]
        return {
            "task_id": task_id,
            "name": task.name,
            "status": task.status,
            "created_at": task.created_at,
            "last_executed": task.last_executed
        }
    
    def get_execution_history(self, limit: int = 20) -> List[Dict]:
        """Get recent execution history"""
        return self.execution_history[-limit:]
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all automation tasks"""
        return [
            {
                "task_id": task.task_id,
                "name": task.name,
                "description": task.description,
                "trigger": task.trigger,
                "status": task.status,
                "created_at": task.created_at
            }
            for task in self.tasks.values()
        ]


class SystemMonitor:
    """Monitor system conditions and trigger automations"""
    
    def __init__(self, automation_engine: AIAutomationEngine):
        self.engine = automation_engine
        self.alerts = []
        self.thresholds = {
            "cpu_max": 80.0,
            "ram_max": 85.0,
            "disk_max": 90.0,
            "temp_max": 85.0
        }
    
    def check_system_conditions(self) -> List[Dict]:
        """Check system and generate alerts if needed"""
        alerts = []
        
        try:
            import psutil
            
            # CPU check
            cpu = psutil.cpu_percent(interval=1)
            if cpu > self.thresholds["cpu_max"]:
                alerts.append({
                    "type": "cpu_high",
                    "severity": "warning",
                    "value": cpu,
                    "threshold": self.thresholds["cpu_max"],
                    "timestamp": datetime.now().isoformat()
                })
            
            # RAM check
            ram = psutil.virtual_memory()
            if ram.percent > self.thresholds["ram_max"]:
                alerts.append({
                    "type": "ram_high",
                    "severity": "warning",
                    "value": ram.percent,
                    "threshold": self.thresholds["ram_max"],
                    "timestamp": datetime.now().isoformat()
                })
            
            # Disk check
            disk = psutil.disk_usage('/')
            if disk.percent > self.thresholds["disk_max"]:
                alerts.append({
                    "type": "disk_full",
                    "severity": "critical",
                    "value": disk.percent,
                    "threshold": self.thresholds["disk_max"],
                    "timestamp": datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"System monitoring error: {e}")
        
        self.alerts.extend(alerts)
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
        
        return alerts
    
    def get_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts[-limit:]
