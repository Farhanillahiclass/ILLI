"""
Computer Control Engine
Manages mouse, keyboard, and application control.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ControlAction(Enum):
    """Types of control actions"""
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_DRAG = "mouse_drag"
    KEYBOARD_TYPE = "keyboard_type"
    KEYBOARD_PRESS = "keyboard_press"
    WINDOW_FOCUS = "window_focus"
    WINDOW_CLOSE = "window_close"
    APP_LAUNCH = "app_launch"
    APP_CLOSE = "app_close"


@dataclass
class ActionResult:
    """Result of a control action"""
    success: bool
    action: ControlAction
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class ControlEngine:
    """
    Main control engine for computer automation.
    """
    
    def __init__(self):
        self._mouse_controller = None
        self._keyboard_controller = None
        self._window_controller = None
        self._initialized = False
        self._action_history: List[ActionResult] = []
        
    async def initialize(self):
        """Initialize the control engine"""
        logger.info("Initializing Control Engine...")
        
        try:
            # Initialize mouse control
            await self._init_mouse()
            
            # Initialize keyboard control
            await self._init_keyboard()
            
            # Initialize window control
            await self._init_window()
            
            self._initialized = True
            logger.info("Control Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Control Engine: {e}")
            raise
    
    async def _init_mouse(self):
        """Initialize mouse control"""
        try:
            import pyautogui
            self._mouse_controller = pyautogui
            # Configure pyautogui
            pyautogui.PAUSE = 0.1
            pyautogui.FAILSAFE = True
            logger.info("Mouse control initialized")
        except ImportError:
            logger.warning("pyautogui not available, using mock mouse")
            self._mouse_controller = "mock"
        except Exception as e:
            logger.error(f"Error initializing mouse: {e}")
            self._mouse_controller = "mock"
    
    async def _init_keyboard(self):
        """Initialize keyboard control"""
        try:
            import keyboard
            self._keyboard_controller = keyboard
            logger.info("Keyboard control initialized")
        except ImportError:
            logger.warning("keyboard not available, using mock keyboard")
            self._keyboard_controller = "mock"
        except Exception as e:
            logger.error(f"Error initializing keyboard: {e}")
            self._keyboard_controller = "mock"
    
    async def _init_window(self):
        """Initialize window control"""
        try:
            import pygetwindow as gw
            self._window_controller = gw
            logger.info("Window control initialized")
        except ImportError:
            logger.warning("pygetwindow not available, using mock window")
            self._window_controller = "mock"
        except Exception as e:
            logger.error(f"Error initializing window: {e}")
            self._window_controller = "mock"
    
    async def move_mouse(self, x: int, y: int, duration: float = 0.5) -> ActionResult:
        """
        Move mouse to position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration in seconds
            
        Returns:
            Action result
        """
        try:
            if self._mouse_controller == "mock":
                logger.info(f"[MOCK] Moving mouse to ({x}, {y})")
                return ActionResult(True, ControlAction.MOUSE_MOVE)
            
            self._mouse_controller.moveTo(x, y, duration=duration)
            logger.info(f"Moved mouse to ({x}, {y})")
            
            result = ActionResult(True, ControlAction.MOUSE_MOVE, metadata={"x": x, "y": y})
            self._action_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Mouse move error: {e}")
            return ActionResult(False, ControlAction.MOUSE_MOVE, error=str(e))
    
    async def click(self, x: Optional[int] = None, y: Optional[int] = None, 
                   button: str = 'left', clicks: int = 1) -> ActionResult:
        """
        Click mouse at position.
        
        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            button: Mouse button ('left', 'right', 'middle')
            clicks: Number of clicks
            
        Returns:
            Action result
        """
        try:
            if self._mouse_controller == "mock":
                logger.info(f"[MOCK] Clicking at ({x}, {y}) with {button} button")
                return ActionResult(True, ControlAction.MOUSE_CLICK)
            
            if x is not None and y is not None:
                self._mouse_controller.click(x, y, button=button, clicks=clicks)
            else:
                self._mouse_controller.click(button=button, clicks=clicks)
            
            logger.info(f"Clicked {button} button {clicks} time(s)")
            
            result = ActionResult(True, ControlAction.MOUSE_CLICK, 
                                metadata={"x": x, "y": y, "button": button, "clicks": clicks})
            self._action_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Click error: {e}")
            return ActionResult(False, ControlAction.MOUSE_CLICK, error=str(e))
    
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                  duration: float = 1.0) -> ActionResult:
        """
        Drag mouse from start to end position.
        
        Args:
            start_x: Start X coordinate
            start_y: Start Y coordinate
            end_x: End X coordinate
            end_y: End Y coordinate
            duration: Drag duration in seconds
            
        Returns:
            Action result
        """
        try:
            if self._mouse_controller == "mock":
                logger.info(f"[MOCK] Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
                return ActionResult(True, ControlAction.MOUSE_DRAG)
            
            self._mouse_controller.dragTo(end_x, end_y, duration=duration, 
                                         button='left')
            logger.info(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
            result = ActionResult(True, ControlAction.MOUSE_DRAG,
                                metadata={"start": (start_x, start_y), "end": (end_x, end_y)})
            self._action_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Drag error: {e}")
            return ActionResult(False, ControlAction.MOUSE_DRAG, error=str(e))
    
    async def type_text(self, text: str, interval: float = 0.0) -> ActionResult:
        """
        Type text using keyboard.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
            
        Returns:
            Action result
        """
        try:
            if self._keyboard_controller == "mock":
                logger.info(f"[MOCK] Typing: {text}")
                return ActionResult(True, ControlAction.KEYBOARD_TYPE)
            
            self._mouse_controller.typewrite(text, interval=interval)
            logger.info(f"Typed: {text}")
            
            result = ActionResult(True, ControlAction.KEYBOARD_TYPE, metadata={"text": text})
            self._action_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Type error: {e}")
            return ActionResult(False, ControlAction.KEYBOARD_TYPE, error=str(e))
    
    async def press_key(self, key: str) -> ActionResult:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'ctrl', 'alt', 'enter', 'f1')
            
        Returns:
            Action result
        """
        try:
            if self._keyboard_controller == "mock":
                logger.info(f"[MOCK] Pressed key: {key}")
                return ActionResult(True, ControlAction.KEYBOARD_PRESS)
            
            self._mouse_controller.press(key)
            logger.info(f"Pressed key: {key}")
            
            result = ActionResult(True, ControlAction.KEYBOARD_PRESS, metadata={"key": key})
            self._action_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Key press error: {e}")
            return ActionResult(False, ControlAction.KEYBOARD_PRESS, error=str(e))
    
    async def hotkey(self, *keys: str) -> ActionResult:
        """
        Press a combination of keys (hotkey).
        
        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
            
        Returns:
            Action result
        """
        try:
            if self._keyboard_controller == "mock":
                logger.info(f"[MOCK] Pressed hotkey: {'+'.join(keys)}")
                return ActionResult(True, ControlAction.KEYBOARD_PRESS)
            
            self._mouse_controller.hotkey(*keys)
            logger.info(f"Pressed hotkey: {'+'.join(keys)}")
            
            result = ActionResult(True, ControlAction.KEYBOARD_PRESS, metadata={"keys": keys})
            self._action_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Hotkey error: {e}")
            return ActionResult(False, ControlAction.KEYBOARD_PRESS, error=str(e))
    
    async def get_mouse_position(self) -> Tuple[int, int]:
        """
        Get current mouse position.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        if self._mouse_controller == "mock":
            return (0, 0)
        
        return self._mouse_controller.position()
    
    async def get_screen_size(self) -> Tuple[int, int]:
        """
        Get screen size.
        
        Returns:
            Tuple of (width, height)
        """
        if self._mouse_controller == "mock":
            return (1920, 1080)
        
        return self._mouse_controller.size()
    
    async def focus_window(self, title: str) -> ActionResult:
        """
        Focus a window by title.
        
        Args:
            title: Window title (partial match)
            
        Returns:
            Action result
        """
        try:
            if self._window_controller == "mock":
                logger.info(f"[MOCK] Focusing window: {title}")
                return ActionResult(True, ControlAction.WINDOW_FOCUS)
            
            windows = self._window_controller.getWindowsWithTitle(title)
            if windows:
                windows[0].activate()
                logger.info(f"Focused window: {title}")
                
                result = ActionResult(True, ControlAction.WINDOW_FOCUS, metadata={"title": title})
                self._action_history.append(result)
                return result
            else:
                logger.warning(f"Window not found: {title}")
                return ActionResult(False, ControlAction.WINDOW_FOCUS, error="Window not found")
        except Exception as e:
            logger.error(f"Window focus error: {e}")
            return ActionResult(False, ControlAction.WINDOW_FOCUS, error=str(e))
    
    async def close_window(self, title: str) -> ActionResult:
        """
        Close a window by title.
        
        Args:
            title: Window title (partial match)
            
        Returns:
            Action result
        """
        try:
            if self._window_controller == "mock":
                logger.info(f"[MOCK] Closing window: {title}")
                return ActionResult(True, ControlAction.WINDOW_CLOSE)
            
            windows = self._window_controller.getWindowsWithTitle(title)
            if windows:
                windows[0].close()
                logger.info(f"Closed window: {title}")
                
                result = ActionResult(True, ControlAction.WINDOW_CLOSE, metadata={"title": title})
                self._action_history.append(result)
                return result
            else:
                logger.warning(f"Window not found: {title}")
                return ActionResult(False, ControlAction.WINDOW_CLOSE, error="Window not found")
        except Exception as e:
            logger.error(f"Window close error: {e}")
            return ActionResult(False, ControlAction.WINDOW_CLOSE, error=str(e))
    
    async def list_windows(self) -> List[Dict[str, Any]]:
        """
        List all open windows.
        
        Returns:
            List of window information
        """
        if self._window_controller == "mock":
            return [
                {"title": "Mock Window 1", "rect": (0, 0, 800, 600)},
                {"title": "Mock Window 2", "rect": (100, 100, 900, 700)}
            ]
        
        windows = self._window_controller.getAllWindows()
        return [
            {
                "title": w.title,
                "rect": (w.left, w.top, w.width, w.height),
                "active": w.isActive
            }
            for w in windows
            if w.title  # Filter out empty titles
        ]
    
    async def launch_application(self, path: str) -> ActionResult:
        """
        Launch an application.
        
        Args:
            path: Path to executable
            
        Returns:
            Action result
        """
        try:
            import subprocess
            subprocess.Popen(path)
            logger.info(f"Launched application: {path}")
            
            result = ActionResult(True, ControlAction.APP_LAUNCH, metadata={"path": path})
            self._action_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Launch error: {e}")
            return ActionResult(False, ControlAction.APP_LAUNCH, error=str(e))
    
    async def get_action_history(self) -> List[ActionResult]:
        """Get history of control actions"""
        return self._action_history
    
    async def clear_action_history(self):
        """Clear action history"""
        self._action_history.clear()
        logger.info("Action history cleared")
    
    async def stop(self):
        """Stop the control engine"""
        logger.info("Control Engine stopped")


class AutomationAgent:
    """
    Agent that performs computer automation tasks.
    """
    
    def __init__(self, control_engine: ControlEngine):
        self.control_engine = control_engine
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        
    async def initialize(self):
        """Initialize the automation agent"""
        await self.control_engine.initialize()
    
    async def start(self):
        """Start the automation agent"""
        self._running = True
        asyncio.create_task(self._task_loop())
        logger.info("Automation agent started")
    
    async def stop(self):
        """Stop the automation agent"""
        self._running = False
        await self.control_engine.stop()
        logger.info("Automation agent stopped")
    
    async def _task_loop(self):
        """Main task processing loop"""
        while self._running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task loop: {e}")
    
    async def _execute_task(self, task: Dict[str, Any]):
        """Execute an automation task"""
        task_type = task.get('type')
        
        if task_type == 'click':
            await self.control_engine.click(
                x=task.get('x'),
                y=task.get('y'),
                button=task.get('button', 'left')
            )
        elif task_type == 'type':
            await self.control_engine.type_text(task.get('text', ''))
        elif task_type == 'press':
            await self.control_engine.press_key(task.get('key'))
        elif task_type == 'hotkey':
            await self.control_engine.hotkey(*task.get('keys', []))
        elif task_type == 'move':
            await self.control_engine.move_mouse(
                x=task.get('x'),
                y=task.get('y')
            )
    
    async def submit_task(self, task: Dict[str, Any]):
        """Submit a task to the automation agent"""
        await self._task_queue.put(task)
    
    async def execute_sequence(self, sequence: List[Dict[str, Any]]) -> List[ActionResult]:
        """
        Execute a sequence of automation tasks.
        
        Args:
            sequence: List of task dictionaries
            
        Returns:
            List of action results
        """
        results = []
        for task in sequence:
            result = await self._execute_task(task)
            results.append(result)
            await asyncio.sleep(task.get('delay', 0.1))
        return results
    
    async def _execute_task(self, task: Dict[str, Any]) -> ActionResult:
        """Execute a single task and return result"""
        task_type = task.get('type')
        
        if task_type == 'click':
            return await self.control_engine.click(
                x=task.get('x'),
                y=task.get('y'),
                button=task.get('button', 'left')
            )
        elif task_type == 'type':
            return await self.control_engine.type_text(task.get('text', ''))
        elif task_type == 'press':
            return await self.control_engine.press_key(task.get('key'))
        elif task_type == 'hotkey':
            return await self.control_engine.hotkey(*task.get('keys', []))
        elif task_type == 'move':
            return await self.control_engine.move_mouse(
                x=task.get('x'),
                y=task.get('y')
            )
        
        return ActionResult(False, ControlAction.MOUSE_CLICK, error="Unknown task type")
