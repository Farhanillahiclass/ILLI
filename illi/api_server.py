"""
REST API Server for ILLI OS
Provides external integration endpoints for remote automation and control
"""

import logging
from typing import Optional, Dict, Any
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class IlliAPIServer:
    """
    FastAPI-based REST server for ILLI OS
    Provides endpoints for external integrations
    """
    
    def __init__(self, automation_engine=None, power_manager=None, voice_engine=None):
        self.automation_engine = automation_engine
        self.power_manager = power_manager
        self.voice_engine = voice_engine
        self.app = None
        self.running = False
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        try:
            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse
            from pydantic import BaseModel
            
            self.app = FastAPI(title="ILLI OS API", version="2.0.0")
            
            # ============ HEALTH CHECK ============
            @self.app.get("/health")
            def health_check():
                """Health check endpoint"""
                return {
                    "status": "ok",
                    "timestamp": datetime.now().isoformat(),
                    "service": "ILLI OS v2.0"
                }
            
            # ============ AUTOMATION ENDPOINTS ============
            class TaskRequest(BaseModel):
                name: str
                description: Optional[str] = None
                trigger: str
                action: str
                parameters: Dict[str, Any]
            
            @self.app.post("/api/tasks/create")
            def create_task(task: TaskRequest):
                """Create new automation task"""
                if not self.automation_engine:
                    raise HTTPException(status_code=503, detail="Automation engine not available")
                
                try:
                    task_id = self.automation_engine.create_task(
                        name=task.name,
                        description=task.description or "",
                        trigger=task.trigger,
                        action=task.action,
                        parameters=task.parameters
                    )
                    return {
                        "status": "created",
                        "task_id": task_id,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            
            @self.app.post("/api/tasks/{task_id}/execute")
            def execute_task(task_id: str):
                """Execute a specific task"""
                if not self.automation_engine:
                    raise HTTPException(status_code=503, detail="Automation engine not available")
                
                result = self.automation_engine.execute_task(task_id)
                return result
            
            @self.app.get("/api/tasks")
            def list_tasks():
                """List all automation tasks"""
                if not self.automation_engine:
                    raise HTTPException(status_code=503, detail="Automation engine not available")
                
                return {
                    "tasks": self.automation_engine.get_all_tasks(),
                    "count": len(self.automation_engine.tasks)
                }
            
            @self.app.get("/api/tasks/{task_id}")
            def get_task_status(task_id: str):
                """Get status of a specific task"""
                if not self.automation_engine:
                    raise HTTPException(status_code=503, detail="Automation engine not available")
                
                return self.automation_engine.get_task_status(task_id)
            
            @self.app.get("/api/execution-history")
            def get_history(limit: int = 20):
                """Get execution history"""
                if not self.automation_engine:
                    raise HTTPException(status_code=503, detail="Automation engine not available")
                
                return {
                    "history": self.automation_engine.get_execution_history(limit),
                    "count": len(self.automation_engine.execution_history)
                }
            
            # ============ NLP PARSING ============
            class CommandRequest(BaseModel):
                command: str
            
            @self.app.post("/api/nlp/parse")
            def parse_nlp_command(req: CommandRequest):
                """Parse natural language command"""
                if not self.automation_engine:
                    raise HTTPException(status_code=503, detail="Automation engine not available")
                
                parsed = self.automation_engine.parse_natural_language(req.command)
                return parsed
            
            # ============ POWER CONTROL ============
            @self.app.post("/api/power/sleep")
            def sleep_system():
                """Put system to sleep"""
                if not self.power_manager:
                    raise HTTPException(status_code=503, detail="Power manager not available")
                
                try:
                    self.power_manager.sleep_system()
                    return {"status": "success", "action": "sleep"}
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            
            @self.app.post("/api/power/restart")
            def restart_system(delay_seconds: int = 10):
                """Restart system"""
                if not self.power_manager:
                    raise HTTPException(status_code=503, detail="Power manager not available")
                
                try:
                    self.power_manager.restart_system(delay_seconds)
                    return {"status": "success", "action": "restart", "delay": delay_seconds}
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            
            @self.app.post("/api/power/shutdown")
            def shutdown_system(delay_seconds: int = 10):
                """Shutdown system"""
                if not self.power_manager:
                    raise HTTPException(status_code=503, detail="Power manager not available")
                
                try:
                    self.power_manager.shutdown_system(delay_seconds)
                    return {"status": "success", "action": "shutdown", "delay": delay_seconds}
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            
            # ============ VOICE CONTROL ============
            class SpeechRequest(BaseModel):
                text: str
                voice_type: Optional[str] = "male"
            
            @self.app.post("/api/voice/speak")
            def text_to_speech(req: SpeechRequest):
                """Convert text to speech"""
                if not self.voice_engine:
                    raise HTTPException(status_code=503, detail="Voice engine not available")
                
                try:
                    if req.voice_type:
                        self.voice_engine.select_voice(req.voice_type)
                    
                    success = self.voice_engine.synthesize_speech(req.text)
                    return {
                        "status": "success" if success else "failed",
                        "text": req.text,
                        "voice": req.voice_type
                    }
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            
            @self.app.get("/api/voice/status")
            def voice_status():
                """Get voice engine status"""
                if not self.voice_engine:
                    raise HTTPException(status_code=503, detail="Voice engine not available")
                
                return {
                    "current_voice": self.voice_engine.current_voice,
                    "available_voices": len(self.voice_engine.available_voices),
                    "voices": self.voice_engine.list_available_voices()[:5]
                }
            
            # ============ SYSTEM INFO ============
            @self.app.get("/api/system/metrics")
            def get_system_metrics():
                """Get current system metrics"""
                try:
                    import psutil
                    cpu = psutil.cpu_percent(interval=0.1)
                    ram = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    return {
                        "cpu": {"percent": cpu, "count": psutil.cpu_count()},
                        "ram": {
                            "percent": ram.percent,
                            "used_gb": round(ram.used / (1024**3), 2),
                            "total_gb": round(ram.total / (1024**3), 2)
                        },
                        "disk": {
                            "percent": disk.percent,
                            "used_gb": round(disk.used / (1024**3), 2),
                            "total_gb": round(disk.total / (1024**3), 2)
                        }
                    }
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))
            
            logger.info("✅ FastAPI routes configured")
            return True
        
        except ImportError:
            logger.warning("FastAPI not available. Install with: pip install fastapi uvicorn")
            return False
        except Exception as e:
            logger.error(f"Failed to setup routes: {e}")
            return False
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the API server in background"""
        if not self.app:
            if not self.setup_routes():
                logger.error("Failed to setup routes")
                return False
        
        try:
            import uvicorn
            
            def start_server():
                self.running = True
                uvicorn.run(
                    self.app,
                    host=host,
                    port=port,
                    log_level="warning"
                )
            
            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()
            
            logger.info(f"✅ API Server started at http://{host}:{port}")
            logger.info(f"📚 API Docs at http://{host}:{port}/docs")
            return True
        
        except ImportError:
            logger.warning("uvicorn not available")
            return False
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            return False


class WebhookManager:
    """Manage webhooks for event-driven automation"""
    
    def __init__(self):
        self.webhooks: Dict[str, list] = {}  # event -> list of webhook URLs
    
    def register_webhook(self, event: str, webhook_url: str) -> bool:
        """Register a webhook for an event"""
        if event not in self.webhooks:
            self.webhooks[event] = []
        
        if webhook_url not in self.webhooks[event]:
            self.webhooks[event].append(webhook_url)
            logger.info(f"Registered webhook for '{event}': {webhook_url}")
            return True
        
        return False
    
    def trigger_webhooks(self, event: str, data: Dict) -> int:
        """Trigger all webhooks for an event"""
        if event not in self.webhooks:
            return 0
        
        triggered = 0
        for webhook_url in self.webhooks[event]:
            try:
                import requests
                requests.post(webhook_url, json=data, timeout=5)
                triggered += 1
            except Exception as e:
                logger.error(f"Webhook trigger failed for {webhook_url}: {e}")
        
        return triggered
    
    def get_webhooks(self, event: Optional[str] = None) -> Dict:
        """Get registered webhooks"""
        if event:
            return {event: self.webhooks.get(event, [])}
        return self.webhooks
