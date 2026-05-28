"""
AI Observability System
Provides monitoring, logging, and analytics for the ILLI system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import psutil
import time

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class LogEntry:
    """A single log entry"""
    timestamp: datetime
    level: LogLevel
    component: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    """A metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    gpu_usage_percent: float
    gpu_memory_used_mb: float
    gpu_memory_total_mb: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: datetime


class ObservabilityEngine:
    """
    Main observability engine for monitoring and analytics.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._logs: List[LogEntry] = []
        self._metrics: List[Metric] = []
        self._events: List[Dict[str, Any]] = []
        self._traces: Dict[str, List[Dict[str, Any]]] = {}
        
        self._max_logs = 10000
        self._max_metrics = 100000
        self._running = False
        self._initialized = False
        
    async def initialize(self):
        """Initialize the observability engine"""
        logger.info("Initializing Observability Engine...")
        
        # Start background collection
        self._running = True
        asyncio.create_task(self._metrics_collection_loop())
        
        self._initialized = True
        logger.info("Observability Engine initialized")
    
    async def log(self, level: LogLevel, component: str, message: str, 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Log a message.
        
        Args:
            level: Log level
            component: Component name
            message: Log message
            metadata: Additional metadata
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            component=component,
            message=message,
            metadata=metadata or {}
        )
        
        self._logs.append(entry)
        
        # Trim if too many logs
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
        
        # Also log to standard logger
        log_func = getattr(logger, level.value, logger.info)
        log_func(f"[{component}] {message}")
    
    async def record_metric(self, name: str, value: float, 
                           metric_type: MetricType = MetricType.GAUGE,
                           labels: Optional[Dict[str, str]] = None):
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Metric labels
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            labels=labels or {}
        )
        
        self._metrics.append(metric)
        
        # Trim if too many metrics
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics:]
    
    async def record_event(self, event_type: str, data: Dict[str, Any]):
        """
        Record an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self._events.append(event)
    
    async def start_trace(self, trace_id: str, operation: str):
        """
        Start a trace for an operation.
        
        Args:
            trace_id: Unique trace identifier
            operation: Operation name
        """
        self._traces[trace_id] = [{
            "operation": operation,
            "start_time": time.time(),
            "type": "start"
        }]
    
    async def end_trace(self, trace_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        End a trace.
        
        Args:
            trace_id: Trace identifier
            metadata: Additional metadata
        """
        if trace_id in self._traces:
            self._traces[trace_id].append({
                "end_time": time.time(),
                "type": "end",
                "metadata": metadata or {}
            })
    
    async def add_trace_span(self, trace_id: str, span_name: str, 
                            metadata: Optional[Dict[str, Any]] = None):
        """
        Add a span to a trace.
        
        Args:
            trace_id: Trace identifier
            span_name: Span name
            metadata: Span metadata
        """
        if trace_id in self._traces:
            self._traces[trace_id].append({
                "span": span_name,
                "time": time.time(),
                "type": "span",
                "metadata": metadata or {}
            })
    
    async def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system metrics.
        
        Returns:
            System metrics
        """
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # GPU (if available)
        gpu_usage_percent = 0.0
        gpu_memory_used_mb = 0.0
        gpu_memory_total_mb = 0.0
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_usage_percent = gpu.load * 100
                gpu_memory_used_mb = gpu.memoryUsed
                gpu_memory_total_mb = gpu.memoryTotal
        except:
            pass
        
        # Network
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / (1024 * 1024)
        network_recv_mb = network.bytes_recv / (1024 * 1024)
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            gpu_usage_percent=gpu_usage_percent,
            gpu_memory_used_mb=gpu_memory_used_mb,
            gpu_memory_total_mb=gpu_memory_total_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            timestamp=datetime.now()
        )
    
    async def _metrics_collection_loop(self):
        """Background loop for collecting metrics"""
        while self._running:
            try:
                # Collect system metrics
                metrics = await self.get_system_metrics()
                
                # Record individual metrics
                await self.record_metric("system_cpu_percent", metrics.cpu_percent, MetricType.GAUGE)
                await self.record_metric("system_memory_percent", metrics.memory_percent, MetricType.GAUGE)
                await self.record_metric("system_disk_percent", metrics.disk_usage_percent, MetricType.GAUGE)
                await self.record_metric("system_gpu_percent", metrics.gpu_usage_percent, MetricType.GAUGE)
                
                await asyncio.sleep(5)  # Collect every 5 seconds
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)
    
    async def get_logs(self, component: Optional[str] = None, 
                      level: Optional[LogLevel] = None,
                      limit: int = 100) -> List[LogEntry]:
        """
        Get logs with optional filtering.
        
        Args:
            component: Filter by component
            level: Filter by log level
            limit: Maximum number of logs to return
            
        Returns:
            Filtered log entries
        """
        logs = self._logs
        
        if component:
            logs = [l for l in logs if l.component == component]
        
        if level:
            logs = [l for l in logs if l.level == level]
        
        return logs[-limit:]
    
    async def get_metrics(self, name: Optional[str] = None,
                         labels: Optional[Dict[str, str]] = None,
                         limit: int = 1000) -> List[Metric]:
        """
        Get metrics with optional filtering.
        
        Args:
            name: Filter by metric name
            labels: Filter by labels
            limit: Maximum number of metrics to return
            
        Returns:
            Filtered metrics
        """
        metrics = self._metrics
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        if labels:
            metrics = [m for m in metrics if all(m.labels.get(k) == v for k, v in labels.items())]
        
        return metrics[-limit:]
    
    async def get_events(self, event_type: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get events with optional filtering.
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            Filtered events
        """
        events = self._events
        
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        
        return events[-limit:]
    
    async def get_trace(self, trace_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get a trace by ID.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Trace data or None
        """
        return self._traces.get(trace_id)
    
    async def export_logs(self, filepath: str):
        """
        Export logs to a file.
        
        Args:
            filepath: Output file path
        """
        logs_data = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "level": entry.level.value,
                "component": entry.component,
                "message": entry.message,
                "metadata": entry.metadata
            }
            for entry in self._logs
        ]
        
        with open(filepath, 'w') as f:
            json.dump(logs_data, f, indent=2)
        
        logger.info(f"Exported {len(logs_data)} logs to {filepath}")
    
    async def export_metrics(self, filepath: str):
        """
        Export metrics to a file.
        
        Args:
            filepath: Output file path
        """
        metrics_data = [
            {
                "name": metric.name,
                "value": metric.value,
                "type": metric.metric_type.value,
                "timestamp": metric.timestamp.isoformat(),
                "labels": metric.labels
            }
            for metric in self._metrics
        ]
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        logger.info(f"Exported {len(metrics_data)} metrics to {filepath}")
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of analytics data.
        
        Returns:
            Analytics summary
        """
        system_metrics = await self.get_system_metrics()
        
        # Count logs by level
        log_counts = {}
        for log in self._logs:
            log_counts[log.level.value] = log_counts.get(log.level.value, 0) + 1
        
        # Count events by type
        event_counts = {}
        for event in self._events:
            event_counts[event["type"]] = event_counts.get(event["type"], 0) + 1
        
        return {
            "system": {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "gpu_percent": system_metrics.gpu_usage_percent
            },
            "logs": {
                "total": len(self._logs),
                "by_level": log_counts
            },
            "metrics": {
                "total": len(self._metrics)
            },
            "events": {
                "total": len(self._events),
                "by_type": event_counts
            },
            "traces": {
                "total": len(self._traces)
            }
        }
    
    async def clear_old_data(self, days: int = 7):
        """
        Clear data older than specified days.
        
        Args:
            days: Number of days to keep
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        # Clear old logs
        self._logs = [l for l in self._logs if l.timestamp > cutoff]
        
        # Clear old metrics
        self._metrics = [m for m in self._metrics if m.timestamp > cutoff]
        
        # Clear old events
        self._events = [e for e in self._events if datetime.fromisoformat(e["timestamp"]) > cutoff]
        
        logger.info(f"Cleared data older than {days} days")
    
    async def stop(self):
        """Stop the observability engine"""
        self._running = False
        logger.info("Observability Engine stopped")


class MonitoringDashboard:
    """
    Provides monitoring data for the dashboard.
    """
    
    def __init__(self, observability: ObservabilityEngine):
        self.observability = observability
        
    async def get_realtime_data(self) -> Dict[str, Any]:
        """
        Get real-time monitoring data.
        
        Returns:
            Real-time data dictionary
        """
        system_metrics = await self.observability.get_system_metrics()
        recent_logs = await self.observability.get_logs(limit=20)
        recent_events = await self.observability.get_events(limit=10)
        
        return {
            "system": {
                "cpu": system_metrics.cpu_percent,
                "memory": system_metrics.memory_percent,
                "gpu": system_metrics.gpu_usage_percent,
                "disk": system_metrics.disk_usage_percent
            },
            "recent_logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level.value,
                    "component": log.component,
                    "message": log.message
                }
                for log in recent_logs
            ],
            "recent_events": recent_events,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_historical_metrics(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get historical metrics for a specific metric.
        
        Args:
            metric_name: Name of the metric
            hours: Number of hours of history
            
        Returns:
            Historical metric data
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        
        metrics = await self.observability.get_metrics(name=metric_name)
        filtered = [m for m in metrics if m.timestamp > cutoff]
        
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "value": m.value,
                "labels": m.labels
            }
            for m in filtered
        ]
