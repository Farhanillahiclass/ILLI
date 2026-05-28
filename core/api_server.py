"""
ILLI API Server
FastAPI server for ILLI backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging

from core.engine import get_engine, EngineState, SystemStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="ILLI API", version="0.1.0")

# Add CORS middleware - must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    response: str
    agent: str
    timestamp: str


class CommandRequest(BaseModel):
    command: str
    params: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    state: str
    model_loaded: bool
    active_agents: int
    memory_usage_mb: float
    cpu_usage_percent: float
    gpu_usage_percent: float
    uptime_seconds: float
    tasks_completed: int
    tasks_failed: int
    last_error: Optional[str]


# Global engine instance
_engine = None


@app.on_event("startup")
async def startup_event():
    """Initialize the engine on startup"""
    global _engine
    logger.info("Starting ILLI API Server...")
    _engine = get_engine()
    await _engine.initialize()
    logger.info("ILLI API Server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the engine on shutdown"""
    global _engine
    if _engine:
        await _engine.stop()
        logger.info("ILLI API Server stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ILLI API Server", "version": "0.1.0"}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    global _engine
    if not _engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    status = _engine.get_status()
    return StatusResponse(
        state=status.state.value,
        model_loaded=status.model_loaded,
        active_agents=status.active_agents,
        memory_usage_mb=status.memory_usage_mb,
        cpu_usage_percent=status.cpu_usage_percent,
        gpu_usage_percent=status.gpu_usage_percent,
        uptime_seconds=status.uptime_seconds,
        tasks_completed=status.tasks_completed,
        tasks_failed=status.tasks_failed,
        last_error=status.last_error
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Submit a query to ILLI"""
    global _engine
    if not _engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        response = await _engine.query(request.query, request.context)
        return QueryResponse(
            response=response.get("response", "No response"),
            agent=response.get("agent", "unknown"),
            timestamp=response.get("timestamp", "")
        )
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/command")
async def command(request: CommandRequest):
    """Execute a command"""
    global _engine
    if not _engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        result = await _engine.command(request.command, request.params)
        return {"result": result}
    except Exception as e:
        logger.error(f"Command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global _engine
    if not _engine:
        return {"status": "unhealthy", "reason": "Engine not initialized"}
    
    return {
        "status": "healthy" if _engine.state == EngineState.RUNNING else "unhealthy",
        "state": _engine.state.value
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
