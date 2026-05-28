"""
Vision Engine
Manages screen capture, OCR, object detection, and image understanding.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionMode(Enum):
    """Vision processing modes"""
    SCREEN_CAPTURE = "screen_capture"
    OCR = "ocr"
    OBJECT_DETECTION = "object_detection"
    UI_ANALYSIS = "ui_analysis"
    IMAGE_UNDERSTANDING = "image_understanding"


@dataclass
class DetectionResult:
    """Result from vision detection"""
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    metadata: Dict[str, Any] = None


@dataclass
class ScreenAnalysis:
    """Complete screen analysis result"""
    text: str
    elements: List[DetectionResult]
    layout: Dict[str, Any]
    timestamp: float


class VisionEngine:
    """
    Main vision engine that handles all vision-related tasks.
    """
    
    def __init__(self):
        self.mode = VisionMode.SCREEN_CAPTURE
        self._ocr_engine = None
        self._object_detector = None
        self._screen_capture = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the vision engine"""
        logger.info("Initializing Vision Engine...")
        
        try:
            # Initialize OCR engine
            await self._init_ocr()
            
            # Initialize object detector
            await self._init_object_detector()
            
            # Initialize screen capture
            await self._init_screen_capture()
            
            self._initialized = True
            logger.info("Vision Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Vision Engine: {e}")
            raise
    
    async def _init_ocr(self):
        """Initialize OCR engine"""
        try:
            import pytesseract
            import cv2
            self._ocr_engine = pytesseract
            logger.info("OCR engine initialized with Tesseract")
        except ImportError:
            logger.warning("Tesseract not available, using mock OCR")
            self._ocr_engine = "mock"
        except Exception as e:
            logger.error(f"Error initializing OCR: {e}")
            self._ocr_engine = "mock"
    
    async def _init_object_detector(self):
        """Initialize object detection model"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLO model...")
            self._object_detector = YOLO('yolov8n.pt')
            logger.info("Object detector initialized")
        except ImportError:
            logger.warning("YOLO not available, using mock detector")
            self._object_detector = "mock"
        except Exception as e:
            logger.error(f"Error initializing object detector: {e}")
            self._object_detector = "mock"
    
    async def _init_screen_capture(self):
        """Initialize screen capture"""
        try:
            import mss
            self._screen_capture = mss.mss()
            logger.info("Screen capture initialized")
        except ImportError:
            logger.warning("mss not available, using mock screen capture")
            self._screen_capture = "mock"
        except Exception as e:
            logger.error(f"Error initializing screen capture: {e}")
            self._screen_capture = "mock"
    
    async def capture_screen(self, monitor: int = 1) -> np.ndarray:
        """
        Capture screen image.
        
        Args:
            monitor: Monitor number to capture
            
        Returns:
            Screen image as numpy array
        """
        if self._screen_capture == "mock":
            # Return a mock image
            return np.zeros((720, 1280, 3), dtype=np.uint8)
        
        try:
            import mss
            monitor_info = self._screen_capture.monitors[monitor]
            screenshot = self._screen_capture.grab(monitor_info)
            
            # Convert to numpy array
            img = np.array(screenshot)
            
            # Remove alpha channel if present
            if img.shape[2] == 4:
                img = img[:, :, :3]
            
            logger.info(f"Screen captured: {img.shape}")
            return img
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return np.zeros((720, 1280, 3), dtype=np.uint8)
    
    async def extract_text(self, image: np.ndarray) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image: Input image
            
        Returns:
            Extracted text
        """
        if self._ocr_engine == "mock":
            return "[MOCK OCR] This is simulated text extraction from image"
        
        try:
            import cv2
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extract text
            text = self._ocr_engine.image_to_string(binary)
            
            logger.info(f"Extracted {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""
    
    async def detect_objects(self, image: np.ndarray, confidence_threshold: float = 0.5) -> List[DetectionResult]:
        """
        Detect objects in image.
        
        Args:
            image: Input image
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of detection results
        """
        if self._object_detector == "mock":
            return [
                DetectionResult(
                    label="mock_object",
                    confidence=0.9,
                    bbox=(100, 100, 200, 200)
                )
            ]
        
        try:
            results = self._object_detector(image, conf=confidence_threshold)
            
            detections = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    label = self._object_detector.names[class_id]
                    
                    detections.append(DetectionResult(
                        label=label,
                        confidence=float(confidence),
                        bbox=(int(x1), int(y1), int(x2 - x1), int(y2 - y1))
                    ))
            
            logger.info(f"Detected {len(detections)} objects")
            return detections
        except Exception as e:
            logger.error(f"Object detection error: {e}")
            return []
    
    async def analyze_screen(self, monitor: int = 1) -> ScreenAnalysis:
        """
        Perform complete screen analysis.
        
        Args:
            monitor: Monitor number to analyze
            
        Returns:
            Complete screen analysis
        """
        import time
        
        # Capture screen
        image = await self.capture_screen(monitor)
        
        # Extract text
        text = await self.extract_text(image)
        
        # Detect objects
        objects = await self.detect_objects(image)
        
        # Analyze layout
        layout = await self._analyze_layout(image, objects)
        
        return ScreenAnalysis(
            text=text,
            elements=objects,
            layout=layout,
            timestamp=time.time()
        )
    
    async def _analyze_layout(self, image: np.ndarray, objects: List[DetectionResult]) -> Dict[str, Any]:
        """
        Analyze the layout of the screen.
        
        Args:
            image: Screen image
            objects: Detected objects
            
        Returns:
            Layout information
        """
        height, width = image.shape[:2]
        
        # Simple layout analysis
        return {
            "width": width,
            "height": height,
            "element_count": len(objects),
            "regions": {
                "top_left": [o for o in objects if o.bbox[0] < width // 2 and o.bbox[1] < height // 2],
                "top_right": [o for o in objects if o.bbox[0] >= width // 2 and o.bbox[1] < height // 2],
                "bottom_left": [o for o in objects if o.bbox[0] < width // 2 and o.bbox[1] >= height // 2],
                "bottom_right": [o for o in objects if o.bbox[0] >= width // 2 and o.bbox[1] >= height // 2],
            }
        }
    
    async def find_element(self, image: np.ndarray, query: str) -> Optional[DetectionResult]:
        """
        Find an element on screen matching the query.
        
        Args:
            image: Screen image
            query: Text or label to search for
            
        Returns:
            Detection result if found, None otherwise
        """
        # Extract text first
        text = await self.extract_text(image)
        
        # Check if query is in text
        if query.lower() in text.lower():
            # Find approximate location (simplified)
            return DetectionResult(
                label=query,
                confidence=0.8,
                bbox=(0, 0, 100, 50),
                metadata={"found_in_text": True}
            )
        
        # Check object labels
        objects = await self.detect_objects(image)
        for obj in objects:
            if query.lower() in obj.label.lower():
                return obj
        
        return None
    
    async def click_element(self, query: str, monitor: int = 1) -> bool:
        """
        Find and click an element on screen.
        
        Args:
            query: Text or label to search for
            monitor: Monitor number
            
        Returns:
            True if click successful
        """
        image = await self.capture_screen(monitor)
        element = await self.find_element(image, query)
        
        if element:
            # Calculate center of bounding box
            x = element.bbox[0] + element.bbox[2] // 2
            y = element.bbox[1] + element.bbox[3] // 2
            
            # Click at position (would use pyautogui)
            logger.info(f"Would click at ({x}, {y})")
            return True
        
        return False
    
    async def understand_image(self, image_path: str) -> str:
        """
        Generate a natural language description of an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image description
        """
        # This would use a vision-language model like BLIP or CLIP
        # For now, return a simple description
        return f"[MOCK] This is an image at {image_path}"
    
    async def save_screenshot(self, path: str, monitor: int = 1):
        """
        Save a screenshot to file.
        
        Args:
            path: Output file path
            monitor: Monitor number
        """
        image = await self.capture_screen(monitor)
        
        import cv2
        cv2.imwrite(path, image)
        logger.info(f"Screenshot saved to {path}")
    
    async def get_screen_text(self, monitor: int = 1) -> str:
        """
        Get all text from screen.
        
        Args:
            monitor: Monitor number
            
        Returns:
            All text on screen
        """
        image = await self.capture_screen(monitor)
        return await self.extract_text(image)
    
    async def stop(self):
        """Stop the vision engine"""
        if self._screen_capture and self._screen_capture != "mock":
            self._screen_capture.close()
        logger.info("Vision Engine stopped")


class VisionAgent:
    """
    Agent that uses vision capabilities to interact with the system.
    """
    
    def __init__(self, vision_engine: VisionEngine):
        self.vision_engine = vision_engine
        self._analysis_history: List[ScreenAnalysis] = []
        
    async def initialize(self):
        """Initialize the vision agent"""
        await self.vision_engine.initialize()
    
    async def look_at_screen(self, monitor: int = 1) -> ScreenAnalysis:
        """Analyze the current screen"""
        analysis = await self.vision_engine.analyze_screen(monitor)
        self._analysis_history.append(analysis)
        return analysis
    
    async def find_and_click(self, query: str, monitor: int = 1) -> bool:
        """Find an element and click it"""
        return await self.vision_engine.click_element(query, monitor)
    
    async def read_screen(self, monitor: int = 1) -> str:
        """Read all text from screen"""
        return await self.vision_engine.get_screen_text(monitor)
    
    async def take_screenshot(self, path: str, monitor: int = 1):
        """Take and save a screenshot"""
        await self.vision_engine.save_screenshot(path, monitor)
    
    def get_analysis_history(self) -> List[ScreenAnalysis]:
        """Get history of screen analyses"""
        return self._analysis_history
    
    async def stop(self):
        """Stop the vision agent"""
        await self.vision_engine.stop()
