"""
ILLI OS v1.2.5 - Complete Launcher
Ultra-robust HUD with all features, comprehensive error handling, and rich diagnostics.
"""

import streamlit as st
import sys
import traceback
from pathlib import Path
from datetime import datetime
import json

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="ILLI OS v1.2.5 - Ghost Protocol HUD",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# SAFE IMPORT HANDLER
# ============================================================================

def safe_import(module_path, name):
    """Safely import module with detailed error reporting"""
    try:
        module = __import__(module_path, fromlist=[name])
        return getattr(module, name)
    except ImportError as e:
        st.error(f"❌ Import failed: {module_path}.{name}\n{str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Error loading {name}: {str(e)}")
        return None

# Load all components
try:
    from illi_ai.interface import (
        inject_ghost_protocol_css,
        render_metric_dial,
        render_neural_core_canvas,
        render_threat_map,
        render_task_tracker,
        render_shell_stream,
        render_three_column_hud,
        initialize_hud_session_state,
        add_shell_log,
        fetch_live_metrics,
        render_whiteboard_hub
    )
    from illi_ai.automation import DeepOSOverlordPowerManager, MasterAgentOrchestrator
    from illi_ai.core import (
        LocalMemorySystem,
        MultiVoiceSynthesisEngine,
        HandshakeDeleteProtection,
        AdaptiveMicrophoneCalibration
    )
    HAS_CORE = True
except Exception as e:
    st.error(f"⚠️ Core modules load error: {str(e)}")
    HAS_CORE = False

# ============================================================================
# SESSION STATE INIT
# ============================================================================

def init_session():
    """Initialize all session state"""
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.hud_active = True
        st.session_state.power_manager = DeepOSOverlordPowerManager()
        st.session_state.memory_system = LocalMemorySystem()
        st.session_state.voice_engine = MultiVoiceSynthesisEngine()
        st.session_state.mic_calibration = AdaptiveMicrophoneCalibration()
        st.session_state.delete_protection = HandshakeDeleteProtection()
        st.session_state.master_agent = MasterAgentOrchestrator(max_workers=4)
        
        st.session_state.active_tab = "dashboard"
        st.session_state.tasks = []
        st.session_state.shell_logs = []
        st.session_state.status_message = "✅ System Ready"
        st.session_state.neural_status = "IDLE"
        st.session_state.is_listening = False
        st.session_state.metrics_history = []
        
        add_shell_log("ILLI OS v1.2.5 initialized", "SUCCESS")
        initialize_hud_session_state()

# ============================================================================
# FEATURE: SYSTEM CONTROL
# ============================================================================

def control_power():
    """Power management controls"""
    st.subheader("⚡ Power Control")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💤 Sleep System", use_container_width=True, key="btn_sleep"):
            add_shell_log("SLEEP initiated", "WARNING")
            st.session_state.power_manager.sleep_system()
    
    with col2:
        if st.button("🔄 Restart", use_container_width=True, key="btn_restart"):
            add_shell_log("RESTART initiated (10s delay)", "WARNING")
            st.session_state.power_manager.restart_system(delay_seconds=10)
    
    with col3:
        if st.button("⛔ Shutdown", use_container_width=True, key="btn_shutdown"):
            add_shell_log("SHUTDOWN initiated (10s delay)", "WARNING")
            st.session_state.power_manager.shutdown_system(delay_seconds=10)
    
    with col4:
        if st.button("🗑️ Clear Recycle", use_container_width=True, key="btn_recycle"):
            if st.session_state.power_manager.clear_recycle_bin():
                add_shell_log("Recycle bin cleared", "SUCCESS")
            else:
                add_shell_log("Recycle bin clear failed", "ERROR")

# ============================================================================
# FEATURE: MICROPHONE & VOICE
# ============================================================================

def control_voice():
    """Voice and microphone controls"""
    st.subheader("🎤 Voice & Audio Control")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎙️ Calibrate Mic", use_container_width=True, key="btn_mic_cal"):
            st.session_state.status_message = "Calibrating microphone..."
            add_shell_log("Microphone calibration started", "INFO")
            try:
                level = st.session_state.mic_calibration.run_ambient_noise_check(duration_seconds=3)
                st.session_state.status_message = f"✅ Calibration complete (Level: {level:.1f})"
                add_shell_log(f"Mic calibrated - Sensitivity: {level:.1f}", "SUCCESS")
            except Exception as e:
                st.session_state.status_message = f"❌ Calibration failed: {str(e)}"
                add_shell_log(f"Calibration error: {str(e)}", "ERROR")
    
    with col2:
        selected_voice = st.radio("Voice:", ["Male", "Female"], horizontal=True, key="radio_voice")
        available_voices = st.session_state.voice_engine.list_available_voices()
        if available_voices:
            visible_names = ", ".join([v["name"] for v in available_voices[:4]])
            st.caption(f"Available voices: {visible_names}{'...' if len(available_voices) > 4 else ''}")
            st.caption(f"Current voice selection: {st.session_state.voice_engine.current_voice.title()}")
        else:
            st.warning("No offline TTS voices detected. Install pyttsx3 or enable Windows voices.")

        if st.button("🗣️ Set Voice", use_container_width=True, key="btn_set_voice"):
            voice_type = selected_voice.lower()
            if st.session_state.voice_engine.select_voice(voice_type):
                add_shell_log(f"Voice switched to {voice_type}", "SUCCESS")
            else:
                add_shell_log(f"Voice {voice_type} not available, using fallback voice", "WARNING")
    
    with col3:
        if st.button("📢 Speak Status", use_container_width=True, key="btn_speak"):
            try:
                metrics = fetch_live_metrics()
                text = f"System status: CPU at {metrics['cpu']:.0f} percent, RAM at {metrics['ram']:.0f} percent"
                success = st.session_state.voice_engine.speak_adaptive(text)
                if success:
                    add_shell_log("Status spoken", "SUCCESS")
                else:
                    add_shell_log("TTS failed; check voice engine and available voices.", "ERROR")
            except Exception as e:
                add_shell_log(f"TTS error: {str(e)}", "ERROR")

# ============================================================================
# FEATURE: APPLICATION LAUNCHER
# ============================================================================

def control_launcher():
    """Application launcher"""
    st.subheader("🚀 Application Launcher")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        app_name = st.text_input("App name:", placeholder="e.g. notepad, calculator, chrome, vscode", key="input_app")
    
    with col2:
        if st.button("Launch", use_container_width=True, key="btn_launch"):
            if app_name.strip():
                if st.session_state.power_manager.launch_application(app_name):
                    add_shell_log(f"Launched: {app_name}", "SUCCESS")
                else:
                    add_shell_log(f"Failed to launch: {app_name}", "ERROR")

# ============================================================================
# FEATURE: FILE SEARCH
# ============================================================================

def control_file_search():
    """File search tool"""
    st.subheader("🔍 File Search")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Search pattern:", placeholder="e.g. *.txt, *.py, document*", key="input_search")
    
    with col2:
        if st.button("Search", use_container_width=True, key="btn_search"):
            if query.strip():
                add_shell_log(f"Searching for: {query}", "INFO")
                try:
                    import fnmatch
                    import os
                    
                    results = []
                    pattern = query.strip()
                    if "*" not in pattern and "?" not in pattern:
                        pattern = f"*{pattern}*"
                    
                    search_paths = [Path.cwd(), Path.home()]
                    for root_path in search_paths:
                        if not root_path.exists():
                            continue
                        try:
                            for root, dirs, files in os.walk(root_path):
                                relative_depth = len(Path(root).relative_to(root_path).parts)
                                if relative_depth > 3:
                                    continue
                                for file in files:
                                    if fnmatch.fnmatch(file.lower(), pattern.lower()):
                                        results.append(os.path.join(root, file))
                                        if len(results) >= 15:
                                            break
                                if len(results) >= 15:
                                    break
                        except Exception:
                            continue
                    
                    if results:
                        add_shell_log(f"Found {len(results)} files", "SUCCESS")
                        with st.expander(f"📁 Results ({len(results)})"):
                            for filepath in results[:15]:
                                st.code(filepath, language="")
                    else:
                        add_shell_log("No files found", "WARNING")
                except Exception as e:
                    add_shell_log(f"Search error: {str(e)}", "ERROR")

# ============================================================================
# FEATURE: SYSTEM DIAGNOSTICS
# ============================================================================

def control_diagnostics():
    """System diagnostics and reports"""
    st.subheader("📊 System Diagnostics")
    st.info("Generate a full system report and it will appear below in JSON format.")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 Full System Report", use_container_width=True, key="btn_diag_full"):
            add_shell_log("Generating system report...", "INFO")
            try:
                report = st.session_state.power_manager.run_system_scan_report()
                report_data = json.loads(report)
                
                st.json(report_data)
                add_shell_log("System report generated", "SUCCESS")
            except Exception as e:
                add_shell_log(f"Report error: {str(e)}", "ERROR")
    
    with col2:
        if st.button("💾 Memory Status", use_container_width=True, key="btn_mem_status"):
            try:
                import psutil
                mem = psutil.virtual_memory()
                st.metric("Memory", f"{mem.percent}%", delta=f"{mem.available / 1024**3:.1f} GB free")
                add_shell_log(f"Memory: {mem.percent}% ({mem.available / 1024**3:.1f} GB free)", "SUCCESS")
            except Exception as e:
                add_shell_log(f"Memory check error: {str(e)}", "ERROR")
    
    with col3:
        if st.button("🌡️ CPU Status", use_container_width=True, key="btn_cpu_status"):
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=1)
                st.metric("CPU", f"{cpu}%")
                add_shell_log(f"CPU: {cpu}%", "SUCCESS")
            except Exception as e:
                add_shell_log(f"CPU check error: {str(e)}", "ERROR")

# ============================================================================
# FEATURE: MEMORY & PREFERENCES
# ============================================================================

def control_preferences():
    """User preferences and memory"""
    st.subheader("👤 Preferences & Memory")
    col1, col2 = st.columns(2)
    
    with col1:
        user_name = st.text_input("Call me:", value=st.session_state.memory_system.get_voice_preference(), key="input_name")
        if st.button("Save Name", use_container_width=True, key="btn_save_name"):
            st.session_state.memory_system.update_voice_preference(user_name)
            add_shell_log(f"Preference saved: Call you '{user_name}'", "SUCCESS")
    
    with col2:
        if st.button("View Preferences", use_container_width=True, key="btn_view_prefs"):
            prefs = st.session_state.memory_system.get_preference("user_call_name", "User")
            st.info(f"📌 You prefer to be called: **{prefs}**")

# ============================================================================
# FEATURE: WALLPAPER
# ============================================================================

def control_wallpaper():
    """Wallpaper generation and control"""
    st.subheader("🎨 Wallpaper Control")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔷 Generate Hex Grid", use_container_width=True, key="btn_wallpaper_hex"):
            try:
                from illi_ai.wallpaper import generate_hex_grid, set_wallpaper
                cache_dir = Path("cache")
                cache_dir.mkdir(exist_ok=True)
                path = generate_hex_grid(str(cache_dir / "hex_grid.png"))
                if set_wallpaper(path):
                    add_shell_log("Hex grid wallpaper applied", "SUCCESS")
                else:
                    add_shell_log("Wallpaper set failed", "ERROR")
            except Exception as e:
                add_shell_log(f"Wallpaper error: {str(e)}", "ERROR")
    
    with col2:
        if st.button("🔴 Generate Red Grid", use_container_width=True, key="btn_wallpaper_red"):
            try:
                from illi_ai.wallpaper import generate_hex_grid, set_wallpaper
                cache_dir = Path("cache")
                cache_dir.mkdir(exist_ok=True)
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (1920, 1920), (0, 0, 0))
                draw = ImageDraw.Draw(img)
                for y in range(0, 1920, 60):
                    for x in range(0, 1920, 60):
                        draw.ellipse((x-15, y-15, x+15, y+15), fill=(255, 50, 50))
                path = cache_dir / "red_grid.png"
                img.save(path)
                if set_wallpaper(str(path)):
                    add_shell_log("Red grid wallpaper applied", "SUCCESS")
                else:
                    add_shell_log("Wallpaper set failed", "ERROR")
            except Exception as e:
                add_shell_log(f"Wallpaper error: {str(e)}", "ERROR")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application logic"""
    if not HAS_CORE:
        st.error("❌ Failed to load core modules. Check imports and try again.")
        return
    
    init_session()
    inject_ghost_protocol_css()
    
    # Header
    st.markdown(
        '<h1 style="text-align: center; color: #00ffff; text-shadow: 0 0 20px #00ffff;">⚙️ ILLI OS v1.2.5</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align: center; color: #00cc99; font-size: 12px;">Ghost-Protocol HUD Matrix | Fully Featured Local AI Agent</p>',
        unsafe_allow_html=True
    )
    
    # Metrics display
    try:
        metrics = fetch_live_metrics()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("CPU", f"{metrics['cpu']:.1f}%")
        with col2:
            st.metric("RAM", f"{metrics['ram']:.1f}%")
        with col3:
            st.metric("Status", st.session_state.status_message.split()[0], delta=st.session_state.neural_status)
        with col4:
            st.metric("Logs", len(st.session_state.shell_logs), delta="entries")
    except Exception as e:
        st.warning(f"⚠️ Metrics error: {str(e)}")
    
    st.divider()
    
    # Tab navigation
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🎯 Dashboard",
        "⚡ Power",
        "🎤 Voice",
        "🚀 Launcher",
        "🔍 Files",
        "📊 Diagnostics",
        "👤 Preferences"
    ])
    
    with tab1:
        st.markdown("### 🎯 Dashboard")
        try:
            left, center, right = st.columns([1, 2, 1])
            with left:
                st.markdown("📈 **System Metrics**")
                st.metric("CPU", f"{metrics['cpu']:.0f}%")
                st.metric("RAM", f"{metrics['ram']:.0f}%")
            with center:
                st.markdown("🧠 **Neural Core Status**")
                st.markdown(
                    render_neural_core_canvas(is_listening=st.session_state.is_listening, status=st.session_state.neural_status),
                    unsafe_allow_html=True
                )
            with right:
                st.markdown("📋 **Activity**")
                st.markdown(render_threat_map(), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Dashboard error: {str(e)}")
    
    with tab2:
        control_power()
    
    with tab3:
        control_voice()
    
    with tab4:
        control_launcher()
    
    with tab5:
        control_file_search()
    
    with tab6:
        control_diagnostics()
    
    with tab7:
        control_preferences()
        st.divider()
        control_wallpaper()
    
    st.divider()
    
    # Shell log display
    st.markdown("### 📡 Shell Stream")
    st.markdown(
        render_shell_stream(st.session_state.shell_logs, max_entries=20),
        unsafe_allow_html=True
    )
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ ILLI OS Info")
        st.markdown("""
        **Version:** 1.2.5  
        **Mode:** Ghost-Protocol HUD  
        **Status:** 🟢 Active  
        **Type:** Local AI Agent
        """)
        
        if st.button("🔄 Refresh", use_container_width=True, key="btn_refresh"):
            st.rerun()
        
        if st.button("🛑 Clear Logs", use_container_width=True, key="btn_clear_logs"):
            st.session_state.shell_logs = []
            st.rerun()

if __name__ == "__main__":
    main()
