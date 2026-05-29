"""
Advanced Local Automation Engine Core
Multi-agent delegation, browser human-simulation, OS control, and voice cognition
"""

import threading
import queue
import subprocess
import psutil
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class AutomationTask:
    """Encapsulate automation task metadata"""
    task_id: str
    name: str
    priority: TaskPriority
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    result: Any = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.kwargs is None:
            self.kwargs = {}


class MasterAgentOrchestrator:
    """
    Master-Agent thread loop for instant UI query feedback (<3s)
    Delegates heavy work to Sub-Agent background pool
    """
    
    def __init__(self, max_workers: int = 4, callback: Optional[Callable] = None):
        self.max_workers = max_workers
        self.callback = callback  # UI callback for status updates
        
        self.task_queue = queue.PriorityQueue()
        self.result_queue = queue.Queue()
        self.worker_threads = []
        self.active_tasks = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self._initialize_worker_pool()
    
    def _initialize_worker_pool(self):
        """Spawn background worker threads"""
        self.is_running = True
        
        # Master-Agent thread (fast response)
        master = threading.Thread(target=self._master_agent_loop, daemon=True)
        master.start()
        self.worker_threads.append(master)
        
        # Sub-Agent worker pool
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._sub_agent_worker, args=(i,), daemon=True)
            worker.start()
            self.worker_threads.append(worker)
        
        logger.info(f"Agent pool initialized: 1 Master + {self.max_workers} Sub-Agents")
    
    def _master_agent_loop(self):
        """Master-Agent: Process high-priority tasks instantly (<3s)"""
        while self.is_running:
            try:
                # Try to get CRITICAL or HIGH priority task
                priority, task = self.task_queue.get(timeout=1)
                
                if priority <= TaskPriority.HIGH.value:
                    # Execute immediately in main thread
                    self._execute_task(task)
                else:
                    # Put back for worker pool
                    self.task_queue.put((priority, task))
                    self.task_queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Master-Agent error: {str(e)}")
    
    def _sub_agent_worker(self, worker_id: int):
        """Sub-Agent worker: Process background/low-priority tasks"""
        while self.is_running:
            try:
                priority, task = self.task_queue.get(timeout=2)
                
                if priority > TaskPriority.HIGH.value:
                    self._execute_task(task, worker_id=worker_id)
                else:
                    # Put back for master
                    self.task_queue.put((priority, task))
                
                self.task_queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Sub-Agent {worker_id} error: {str(e)}")
    
    def _execute_task(self, task: AutomationTask, worker_id: int = -1):
        """Execute automation task with error handling"""
        try:
            task.status = "RUNNING"
            task.started_at = time.time()
            
            with self.lock:
                self.active_tasks[task.task_id] = task
            
            # UI callback: task started
            if self.callback:
                self.callback({
                    "type": "task_started",
                    "task_id": task.task_id,
                    "name": task.name,
                    "worker_id": worker_id,
                })
            
            # Execute task
            result = task.func(*task.args, **task.kwargs)
            
            task.status = "COMPLETED"
            task.result = result
            task.completed_at = time.time()
            
            # UI callback: task completed
            if self.callback:
                self.callback({
                    "type": "task_completed",
                    "task_id": task.task_id,
                    "name": task.name,
                    "result": result,
                    "duration": task.completed_at - task.started_at,
                })
        
        except Exception as e:
            task.status = "FAILED"
            task.error = str(e)
            task.completed_at = time.time()
            
            logger.error(f"Task {task.task_id} failed: {str(e)}")
            
            if self.callback:
                self.callback({
                    "type": "task_failed",
                    "task_id": task.task_id,
                    "name": task.name,
                    "error": str(e),
                })
    
    def submit_task(self, task: AutomationTask) -> str:
        """Submit task to agent pool"""
        priority_value = task.priority.value
        self.task_queue.put((priority_value, task))
        return task.task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel pending/running task"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.status == "PENDING":
                    task.status = "CANCELLED"
                    return True
                elif task.status == "RUNNING":
                    # Attempt graceful cancellation
                    task.status = "CANCELLED"
                    logger.info(f"Task {task_id} marked for cancellation")
                    return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status and metadata"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return {
                    "task_id": task.task_id,
                    "name": task.name,
                    "status": task.status,
                    "priority": task.priority.name,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "result": task.result,
                    "error": task.error,
                }
        return None
    
    def shutdown(self):
        """Gracefully shutdown agent pool"""
        self.is_running = False
        for thread in self.worker_threads:
            thread.join(timeout=2)
        logger.info("Agent pool shutdown complete")


class SandboxBrowserAutomationEngine:
    """
    Persistent browser automation with human-simulation via PyAutoGUI
    Takes screenshots, computes pixel coordinates, simulates human interaction
    """
    
    def __init__(self, profile_dir: Optional[Path] = None):
        self.profile_dir = profile_dir or Path.home() / ".illi_browser_profiles"
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        
        # Attempt imports
        try:
            from playwright.async_api import async_playwright
            self.playwright_available = True
        except ImportError:
            logger.warning("Playwright not available; browser automation disabled")
            self.playwright_available = False
        
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.pyautogui_available = True
        except ImportError:
            logger.warning("PyAutoGUI not available; GUI automation disabled")
            self.pyautogui_available = False
    
    def take_screenshot(self, filepath: Path) -> bool:
        """Take browser/screen screenshot"""
        if not self.pyautogui_available:
            logger.error("PyAutoGUI not available for screenshots")
            return False
        
        try:
            screenshot = self.pyautogui.screenshot()
            screenshot.save(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            return False
    
    def compute_pixel_coordinates(self, element_description: str) -> Optional[tuple]:
        """
        Use OCR/template matching to locate element pixel coordinates
        This is a placeholder; in production use pytesseract + cv2
        """
        if not self.pyautogui_available:
            return None
        
        try:
            # Placeholder: Find text on screen
            location = self.pyautogui.locateOnScreen(element_description, confidence=0.8)
            if location:
                return (location[0] + location[2]//2, location[1] + location[3]//2)
        except Exception as e:
            logger.debug(f"Element search failed: {str(e)}")
        
        return None
    
    def simulate_click(self, x: int, y: int, delay: float = 0.2) -> bool:
        """Simulate human mouse click"""
        if not self.pyautogui_available:
            return False
        
        try:
            self.pyautogui.moveTo(x, y, duration=delay)
            self.pyautogui.click()
            time.sleep(delay)
            logger.info(f"Click simulated at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Click simulation failed: {str(e)}")
            return False
    
    def simulate_typing(self, text: str, interval: float = 0.05) -> bool:
        """Simulate human typing with variable interval"""
        if not self.pyautogui_available:
            return False
        
        try:
            self.pyautogui.typewrite(text, interval=interval)
            logger.info(f"Typed: {text}")
            return True
        except Exception as e:
            logger.error(f"Typing simulation failed: {str(e)}")
            return False
    
    def simulate_scroll(self, x: int, y: int, direction: str = "down", amount: int = 3) -> bool:
        """Simulate scrolling (direction: 'up' or 'down')"""
        if not self.pyautogui_available:
            return False
        
        try:
            self.pyautogui.moveTo(x, y)
            scroll_amount = amount if direction == "down" else -amount
            self.pyautogui.scroll(scroll_amount)
            logger.info(f"Scrolled {direction} by {amount} ticks")
            return True
        except Exception as e:
            logger.error(f"Scroll simulation failed: {str(e)}")
            return False
    
    def extract_to_markdown(self, content: str, title: str, output_path: Path) -> bool:
        """Export extracted content to structured Markdown"""
        try:
            md_content = f"""# ILLI OS Automation Report
**Generated**: {datetime.now().isoformat()}
**Title**: {title}

## Extracted Content

{content}

---
*Report generated by ILLI OS v1.2.5 Sandbox Browser Automation Engine*
"""
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(md_content, encoding='utf-8')
            logger.info(f"Report exported: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Markdown export failed: {str(e)}")
            return False


class DeepOSOverlordPowerManager:
    """
    Direct administrative-level OS control
    Wallpaper, Sleep, Reboot, Shutdown, Audio Mute, Recycle Bin
    """
    
    @staticmethod
    def set_wallpaper(image_path: Path) -> bool:
        """Set Windows desktop wallpaper"""
        try:
            import ctypes
            image_path_str = str(image_path.resolve())
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path_str, 3)
            logger.info(f"Wallpaper set: {image_path_str}")
            return True
        except Exception as e:
            logger.error(f"Wallpaper set failed: {str(e)}")
            return False
    
    @staticmethod
    def sleep_system() -> bool:
        """Put system to sleep"""
        try:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            logger.info("System sleep initiated")
            return True
        except Exception as e:
            logger.error(f"Sleep failed: {str(e)}")
            return False
    
    @staticmethod
    def restart_system(delay_seconds: int = 5) -> bool:
        """Restart system with delay"""
        try:
            subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], check=True)
            logger.info(f"Restart scheduled in {delay_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Restart failed: {str(e)}")
            return False
    
    @staticmethod
    def shutdown_system(delay_seconds: int = 5) -> bool:
        """Shutdown system with delay"""
        try:
            subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], check=True)
            logger.info(f"Shutdown scheduled in {delay_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Shutdown failed: {str(e)}")
            return False
    
    @staticmethod
    def toggle_audio_mute(mute: bool = True) -> bool:
        """Toggle system audio mute state"""
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMute(mute, None)
            logger.info(f"Audio {'muted' if mute else 'unmuted'}")
            return True
        except Exception as e:
            logger.warning(f"Audio control unavailable: {str(e)}")
            return False
    
    @staticmethod
    def clear_recycle_bin() -> bool:
        """Permanently clear Windows Recycle Bin"""
        try:
            import ctypes
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
            logger.info("Recycle Bin cleared")
            return True
        except Exception as e:
            logger.error(f"Recycle Bin clear failed: {str(e)}")
            return False
    
    @staticmethod
    def launch_application(app_name: str) -> bool:
        """Launch application by name or path"""
        try:
            # Try direct launch
            try:
                subprocess.Popen(app_name)
                logger.info(f"Launched: {app_name}")
                return True
            except FileNotFoundError:
                # Search in PATH
                from shutil import which
                app_path = which(app_name)
                if app_path:
                    subprocess.Popen(app_path)
                    logger.info(f"Launched: {app_path}")
                    return True
        except Exception as e:
            logger.error(f"Application launch failed: {str(e)}")
            return False
    
    @staticmethod
    def run_system_scan_report() -> str:
        """Generate comprehensive system diagnostics report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total_gb": psutil.virtual_memory().total / (1024**3),
                    "available_gb": psutil.virtual_memory().available / (1024**3),
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    drive: {
                        "total_gb": psutil.disk_usage(f"{drive}:\\").total / (1024**3),
                        "free_gb": psutil.disk_usage(f"{drive}:\\").free / (1024**3),
                        "percent": psutil.disk_usage(f"{drive}:\\").percent,
                    }
                    for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ"
                    if os.path.exists(f"{drive}:\\")
                },
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            }
            logger.info("System scan report generated")
            return json.dumps(report, indent=2)
        except Exception as e:
            logger.error(f"System scan failed: {str(e)}")
            return ""


# Global automation instances
_master_agent: Optional[MasterAgentOrchestrator] = None
_browser_engine: Optional[SandboxBrowserAutomationEngine] = None
_power_manager = DeepOSOverlordPowerManager()


def get_master_agent(callback: Optional[Callable] = None) -> MasterAgentOrchestrator:
    """Get or create master agent orchestrator"""
    global _master_agent
    if _master_agent is None:
        _master_agent = MasterAgentOrchestrator(callback=callback)
    return _master_agent


def get_browser_engine() -> SandboxBrowserAutomationEngine:
    """Get or create browser automation engine"""
    global _browser_engine
    if _browser_engine is None:
        _browser_engine = SandboxBrowserAutomationEngine()
    return _browser_engine
