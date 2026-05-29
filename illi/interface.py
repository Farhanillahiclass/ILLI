"""
Ghost-Protocol HUD Matrix Interface
Advanced cyberpunk UI with dense HTML5/CSS injections for ILLI OS v1.2.5
"""

import streamlit as st
import psutil
import json
import time
from datetime import datetime
from pathlib import Path

# ============================================================================
# GHOST-PROTOCOL CSS INJECTION & LAYOUT MASKING
# ============================================================================

GHOST_PROTOCOL_CSS = """
<style>
    /* MASK DEFAULT STREAMLIT LAYOUT */
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }
    .st-emotion-cache-1y4p8pa { display: none !important; }
    .st-emotion-cache-z5fcl4 { display: none !important; }
    .stToolbar { display: none !important; }
    .stDeployButton { display: none !important; }
    footer { display: none !important; }
    .st-emotion-cache-ocqkz7 { padding: 0 !important; margin: 0 !important; }
    
    /* HEXAGONAL MESH GRID BACKGROUND */
    body, [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        background-image: 
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 35px,
                rgba(0, 255, 255, 0.03) 35px,
                rgba(0, 255, 255, 0.03) 70px
            ),
            repeating-linear-gradient(
                60deg,
                transparent,
                transparent 35px,
                rgba(0, 255, 255, 0.02) 35px,
                rgba(0, 255, 255, 0.02) 70px
            ),
            repeating-linear-gradient(
                120deg,
                transparent,
                transparent 35px,
                rgba(0, 255, 255, 0.02) 35px,
                rgba(0, 255, 255, 0.02) 70px
            );
        color: #00ffff;
        font-family: 'Courier New', monospace;
    }
    
    /* PULSING NEON HEXAGON ACCENT */
    @keyframes hexPulse {
        0%, 100% { border-color: rgba(0, 255, 255, 0.3); box-shadow: 0 0 10px rgba(0, 255, 255, 0.1); }
        50% { border-color: rgba(0, 255, 255, 0.8); box-shadow: 0 0 20px rgba(0, 255, 255, 0.4); }
    }
    
    /* MAIN CONTAINER STYLING */
    [data-testid="stMainBlockContainer"] {
        padding: 0 !important;
        max-width: 100%;
        background: rgba(0, 0, 0, 0.95);
    }
    
    /* THREE-COLUMN ASYMMETRIC LAYOUT */
    .three-column-matrix {
        display: grid;
        grid-template-columns: 1fr 1.2fr 0.9fr;
        gap: 15px;
        padding: 20px;
        width: 100%;
        height: auto;
    }
    
    /* GLASSMORPHISM PANELS */
    .hud-panel {
        background: rgba(10, 10, 25, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 255, 255, 0.1);
        animation: hexPulse 3s ease-in-out infinite;
    }
    
    /* LEFT PANEL: HARDWARE TELEMETRY */
    .left-hud {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    
    .metric-dial {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 15px;
        border: 2px solid rgba(0, 255, 255, 0.3);
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0, 255, 255, 0.1) 0%, rgba(0, 0, 0, 0.9) 100%);
        aspect-ratio: 1;
        transition: all 0.3s ease;
    }
    
    .metric-dial:hover {
        border-color: rgba(0, 255, 255, 0.8);
        box-shadow: inset 0 0 15px rgba(0, 255, 255, 0.2);
    }
    
    .metric-label {
        font-size: 0.8em;
        color: rgba(0, 255, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .metric-value {
        font-size: 2.5em;
        color: #00ffff;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    }
    
    /* CENTER PANEL: NEURAL CORE */
    .center-hub {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 20px;
    }
    
    .neural-core-canvas {
        width: 100%;
        height: 300px;
        border: 2px solid rgba(0, 255, 255, 0.3);
        border-radius: 12px;
        background: radial-gradient(circle, rgba(0, 50, 80, 0.3) 0%, rgba(0, 0, 0, 0.9) 100%);
        position: relative;
    }
    
    /* NEURAL CORE STATE TRANSITIONS */
    .neural-active { animation: neuroActivate 0.6s ease-out; }
    .neural-listening { animation: neuroListening 0.8s ease-in-out infinite; }
    
    @keyframes neuroActivate {
        0% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 255, 0.7); }
        100% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }
    }
    
    @keyframes neuroListening {
        0%, 100% { border-color: rgba(255, 0, 0, 0.4); box-shadow: 0 0 20px rgba(255, 0, 0, 0.2); }
        50% { border-color: rgba(255, 50, 50, 0.8); box-shadow: 0 0 40px rgba(255, 50, 50, 0.5); }
    }
    
    /* RIGHT PANEL: MODULAR TABS */
    .right-modular {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .tab-container {
        display: flex;
        gap: 5px;
        margin-bottom: 10px;
        flex-wrap: wrap;
    }
    
    .tab-button {
        padding: 8px 12px;
        background: rgba(0, 255, 255, 0.1);
        border: 1px solid rgba(0, 255, 255, 0.3);
        color: #00ffff;
        cursor: pointer;
        border-radius: 4px;
        font-size: 0.85em;
        transition: all 0.2s;
        text-transform: uppercase;
    }
    
    .tab-button:hover, .tab-button.active {
        background: rgba(0, 255, 255, 0.3);
        border-color: rgba(0, 255, 255, 0.8);
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    }
    
    .tab-content {
        background: rgba(5, 15, 30, 0.6);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 6px;
        padding: 12px;
        min-height: 200px;
        overflow-y: auto;
        max-height: 250px;
        font-size: 0.85em;
    }
    
    /* THREAT MAP VISUAL */
    .threat-map {
        width: 100%;
        height: 150px;
        background: radial-gradient(circle, rgba(0, 100, 50, 0.2) 0%, rgba(0, 0, 0, 0.9) 100%);
        border: 1px solid rgba(0, 255, 100, 0.3);
        border-radius: 6px;
        position: relative;
        overflow: hidden;
    }
    
    .threat-marker {
        position: absolute;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: threatPulse 2s ease-in-out infinite;
    }
    
    .threat-positive {
        background: rgba(0, 255, 0, 0.7);
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
    }
    
    .threat-negative {
        background: rgba(255, 50, 50, 0.7);
        box-shadow: 0 0 10px rgba(255, 50, 50, 0.5);
    }
    
    @keyframes threatPulse {
        0%, 100% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.5); opacity: 1; }
    }
    
    /* TASK TRACKER */
    .task-item {
        padding: 8px;
        margin: 4px 0;
        background: rgba(0, 255, 255, 0.05);
        border-left: 3px solid rgba(0, 255, 255, 0.3);
        border-radius: 2px;
        font-size: 0.8em;
        transition: all 0.2s;
    }
    
    .task-item:hover {
        background: rgba(0, 255, 255, 0.1);
        border-left-color: rgba(0, 255, 255, 0.8);
    }
    
    .task-completed {
        opacity: 0.5;
        text-decoration: line-through;
    }
    
    /* BOTTOM SHELL STREAM */
    .bottom-shell-stream {
        margin-top: 20px;
        padding: 15px;
        background: rgba(0, 5, 15, 0.8);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 0.8em;
        color: rgba(0, 255, 200, 0.9);
        max-height: 150px;
        overflow-y: auto;
        line-height: 1.6;
    }
    
    .log-entry {
        margin: 4px 0;
        padding: 2px 0;
        border-bottom: 1px solid rgba(0, 255, 255, 0.1);
    }
    
    .log-timestamp {
        color: rgba(0, 255, 255, 0.5);
    }
    
    .log-level-core {
        color: rgba(0, 255, 255, 0.8);
    }
    
    .log-level-error {
        color: rgba(255, 50, 50, 0.9);
    }
    
    .log-level-success {
        color: rgba(0, 255, 100, 0.8);
    }
    
    /* RESPONSIVE ADJUSTMENTS */
    @media (max-width: 1600px) {
        .three-column-matrix {
            grid-template-columns: 0.9fr 1fr 0.8fr;
            gap: 10px;
            padding: 15px;
        }
    }
    
    @media (max-width: 1200px) {
        .three-column-matrix {
            grid-template-columns: 1fr;
            gap: 15px;
        }
    }
</style>
"""


def inject_ghost_protocol_css():
    """Inject Ghost-Protocol CSS into Streamlit HUD"""
    st.markdown(GHOST_PROTOCOL_CSS, unsafe_allow_html=True)


def render_metric_dial(label: str, value: float, max_value: float = 100.0, unit: str = "%") -> str:
    """Render animated circular metric dial"""
    percentage = min(100, (value / max_value) * 100)
    angle = (percentage / 100) * 360
    
    html = f"""
    <div class="metric-dial">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value:.0f}{unit}</div>
        <div style="font-size: 0.7em; color: rgba(0, 255, 255, 0.5);">{percentage:.0f}% of {max_value:.0f}</div>
    </div>
    """
    return html


def render_neural_core_canvas(is_listening: bool = False, status: str = "IDLE") -> str:
    """Render 3D rotating neural core with particle field"""
    animation_class = "neural-listening" if is_listening else "neural-active"
    border_color = "rgba(255, 50, 50, 0.5)" if is_listening else "rgba(0, 255, 255, 0.3)"
    
    html = f"""
    <div class="neural-core-canvas {animation_class}" style="border-color: {border_color};">
        <canvas id="neuralCoreCanvas" style="width: 100%; height: 100%;"></canvas>
        <div style="position: absolute; bottom: 10px; right: 10px; font-size: 0.7em; color: rgba(0, 255, 255, 0.6);">
            [{status}]
        </div>
    </div>
    <script>
        function renderNeuralCore() {{
            const canvas = document.getElementById('neuralCoreCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = Math.min(canvas.width, canvas.height) / 2 - 20;
            const time = Date.now() / 1000;
            
            // Clear canvas
            ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw rotating wireframe sphere
            ctx.strokeStyle = 'rgba(0, 255, 255, 0.4)';
            ctx.lineWidth = 1.5;
            
            const rings = 5;
            const segments = 16;
            
            for (let ring = 0; ring < rings; ring++) {{
                const ringRadius = (radius * (ring + 1)) / rings;
                const lat = (ring / rings) * Math.PI;
                
                for (let seg = 0; seg < segments; seg++) {{
                    const lon = (seg / segments) * Math.PI * 2 + time;
                    const nextLon = ((seg + 1) / segments) * Math.PI * 2 + time;
                    
                    const x1 = centerX + ringRadius * Math.sin(lat) * Math.cos(lon);
                    const y1 = centerY + ringRadius * Math.cos(lat);
                    const x2 = centerX + ringRadius * Math.sin(lat) * Math.cos(nextLon);
                    const y2 = centerY + ringRadius * Math.cos(lat);
                    
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                }}
            }}
            
            // Draw core particle nucleus
            ctx.fillStyle = 'rgba(0, 255, 255, 0.8)';
            ctx.beginPath();
            ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
            ctx.fill();
            
            requestAnimationFrame(renderNeuralCore);
        }}
        renderNeuralCore();
    </script>
    """
    return html


def render_threat_map() -> str:
    """Render interactive global threat marker map"""
    markers = [
        {"x": "15%", "y": "25%", "type": "positive", "label": "✓ Secure"},
        {"x": "35%", "y": "45%", "type": "negative", "label": "✗ Alert"},
        {"x": "65%", "y": "30%", "type": "positive", "label": "✓ Clean"},
        {"x": "80%", "y": "70%", "type": "negative", "label": "✗ Warning"},
    ]
    
    html = '<div class="threat-map">'
    for marker in markers:
        html += f"""
        <div class="threat-marker threat-{marker['type']}" 
             style="left: {marker['x']}; top: {marker['y']};" 
             title="{marker['label']}"></div>
        """
    html += '</div>'
    return html


def render_task_tracker(tasks: list) -> str:
    """Render task checklist tracker"""
    html = '<div>'
    if not tasks:
        html += '<div style="color: rgba(0, 255, 255, 0.5); padding: 10px;">No tasks. System idle.</div>'
    else:
        for idx, task in enumerate(tasks):
            completed_class = "task-completed" if task.get("completed", False) else ""
            html += f'<div class="task-item {completed_class}">• {task.get("text", "Unknown Task")}</div>'
    html += '</div>'
    return html

def render_whiteboard_hub() -> str:
    """Render a mock technical whiteboard flowchart"""
    html = """
    <div style="height: 180px; width: 100%; border: 1px dashed rgba(0, 255, 255, 0.3); position: relative; background: rgba(0,20,40,0.2);">
        <svg width="100%" height="100%" viewBox="0 0 200 100">
            <rect x="10" y="40" width="40" height="20" rx="2" fill="none" stroke="#00ffff" stroke-width="0.5" />
            <text x="15" y="52" fill="#00ffff" font-size="5">CORE_INIT</text>
            
            <line x1="50" y1="50" x2="80" y2="50" stroke="#00ffff" stroke-width="0.5" stroke-dasharray="2,2" />
            
            <rect x="80" y="30" width="40" height="40" rx="2" fill="none" stroke="#00ffff" stroke-width="0.5" />
            <text x="85" y="45" fill="#00ffff" font-size="4">NEURAL_PROC</text>
            <circle cx="100" cy="55" r="5" fill="none" stroke="#00ffff" stroke-width="0.3" />
            
            <line x1="120" y1="50" x2="150" y2="50" stroke="#00ffff" stroke-width="0.5" stroke-dasharray="2,2" />
            
            <rect x="150" y="40" width="40" height="20" rx="2" fill="none" stroke="#00ffff" stroke-width="0.5" />
            <text x="155" y="52" fill="#00ffff" font-size="5">OUT_RELAY</text>
        </svg>
        <div style="position: absolute; top: 5px; left: 5px; font-size: 0.6em; color: rgba(0, 255, 255, 0.5);">[SYSTEM_DIAGRAM_V1]</div>
    </div>
    """
    return html

def render_shell_stream(log_entries: list, max_entries: int = 15) -> str:
    """Render bottom shell stream with synchronized timestamps"""
    html = '<div class="bottom-shell-stream">'
    
    for entry in log_entries[-max_entries:]:
        timestamp = entry.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        level = entry.get("level", "INFO")
        message = entry.get("message", "")
        
        level_class = f"log-level-{level.lower()}"
        html += f"""
        <div class="log-entry">
            <span class="log-timestamp">[{timestamp}]</span>
            <span class="{level_class}"> [{level}]:</span>
            {message}
        </div>
        """
    
    html += '</div>'
    return html


def initialize_hud_session_state():
    """Initialize Ghost-Protocol HUD session state variables"""
    defaults = {
        "hud_active": True,
        "mic_listening": False,
        "neural_status": "IDLE",
        "active_tab": "threat_hub",
        "tasks": [],
        "shell_logs": [],
        "system_metrics": {"cpu": 0, "ram": 0},
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_shell_log(message: str, level: str = "INFO"):
    """Add entry to shell stream log"""
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message,
    }
    if "shell_logs" not in st.session_state:
        st.session_state["shell_logs"] = []
    st.session_state["shell_logs"].append(entry)
    # Keep only last 50 entries
    if len(st.session_state["shell_logs"]) > 50:
        st.session_state["shell_logs"] = st.session_state["shell_logs"][-50:]


def fetch_live_metrics() -> dict:
    """Fetch live system metrics for HUD telemetry"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        
        # Network I/O
        net_io = psutil.net_io_counters()
        
        return {
            "cpu": cpu_percent,
            "ram": ram_percent,
            "net_bytes_sent": net_io.bytes_sent,
            "net_bytes_recv": net_io.bytes_recv,
        }
    except Exception as e:
        add_shell_log(f"Metrics fetch error: {str(e)}", "ERROR")
        return {"cpu": 0, "ram": 0}


def render_three_column_hud(left_content: str, center_content: str, right_content: str) -> None:
    """Render the three-column asymmetric HUD layout"""
    html = f"""
    <div class="three-column-matrix">
        <div class="hud-panel left-hud">
            {left_content}
        </div>
        <div class="hud-panel center-hub">
            {center_content}
        </div>
        <div class="hud-panel right-modular">
            {right_content}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
