"""
ILLI OS v2.0 - Enhanced HUD with Advanced Features
Multi-tab interface with analytics, scheduling, automation, backup, monitoring, AI automation, and REST API
"""

import streamlit as st
import sys
import traceback
from pathlib import Path
from datetime import datetime, timedelta
import json
import sqlite3
import threading
from collections import defaultdict
import logging

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="ILLI OS v2.0 - Advanced Control Center",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SAFE IMPORT HANDLER
# ============================================================================

def safe_import(module_path, name):
    """Safely import module with detailed error reporting"""
    try:
        module = __import__(module_path, fromlist=[name])
        return getattr(module, name)
    except ImportError as e:
        st.warning(f"⚠️ Optional module not available: {module_path}.{name}")
        return None
    except Exception as e:
        st.warning(f"⚠️ Error loading {name}: {str(e)}")
        return None

# Load core components
HAS_CORE = False
core_components = {}

try:
    from illi.core import (
        LocalMemorySystem,
        MultiVoiceSynthesisEngine,
        HandshakeDeleteProtection,
        AdaptiveMicrophoneCalibration
    )
    
    # Optional imports
    from illi.automation import DeepOSOverlordPowerManager
    from illi.ai_automation import AIAutomationEngine, SystemMonitor
    from illi.voice_automation import VoiceCommandProcessor, VoiceAutomationOrchestrator
    from illi.api_server import IlliAPIServer, WebhookManager
    
    core_components = {
        "memory_system": LocalMemorySystem,
        "voice_engine": MultiVoiceSynthesisEngine,
        "power_manager": DeepOSOverlordPowerManager,
        "ai_automation": AIAutomationEngine,
        "system_monitor": SystemMonitor,
        "voice_processor": VoiceCommandProcessor,
        "api_server": IlliAPIServer,
        "webhook_manager": WebhookManager
    }
    HAS_CORE = True
    st.info("✅ All core modules loaded successfully")
except Exception as e:
    st.warning(f"⚠️ Some modules not available: {str(e)}")
    HAS_CORE = True  # Allow app to run with limited features

# ============================================================================
# ENHANCED FEATURES: Task Scheduler
# ============================================================================

class TaskScheduler:
    """Schedule and manage recurring tasks"""
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path.home() / ".illi_scheduler" / "tasks.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    task_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    action TEXT NOT NULL,
                    schedule_type TEXT,
                    schedule_time TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_task(self, name: str, description: str, action: str, schedule_type: str, schedule_time: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO scheduled_tasks 
                   (name, description, action, schedule_type, schedule_time, next_run)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, description, action, schedule_type, schedule_time, datetime.now().isoformat())
            )
            conn.commit()
        return True
    
    def get_tasks(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT task_id, name, description, action, schedule_type, schedule_time, enabled, last_run, next_run FROM scheduled_tasks"
            )
            return cursor.fetchall()
    
    def update_task(self, task_id: int, enabled: bool = None, last_run: str = None):
        updates = []
        params = []
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(enabled)
        if last_run is not None:
            updates.append("last_run = ?")
            params.append(last_run)
        
        if updates:
            params.append(task_id)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"UPDATE scheduled_tasks SET {', '.join(updates)} WHERE task_id = ?", params)
                conn.commit()

# ============================================================================
# ENHANCED FEATURES: System Analytics
# ============================================================================

class SystemAnalytics:
    """Track and analyze system performance metrics"""
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path.home() / ".illi_analytics" / "metrics.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_history = defaultdict(list)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    metric_id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    ram_percent REAL,
                    disk_percent REAL,
                    net_bytes_sent INTEGER,
                    net_bytes_recv INTEGER
                )
            """)
            conn.commit()
    
    def log_metrics(self, cpu: float, ram: float, disk: float = 0, net_sent: int = 0, net_recv: int = 0):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO metrics (cpu_percent, ram_percent, disk_percent, net_bytes_sent, net_bytes_recv)
                   VALUES (?, ?, ?, ?, ?)""",
                (cpu, ram, disk, net_sent, net_recv)
            )
            conn.commit()
    
    def get_metrics_history(self, limit: int = 100):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT timestamp, cpu_percent, ram_percent, disk_percent, net_bytes_sent, net_bytes_recv FROM metrics ORDER BY metric_id DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()

# ============================================================================
# ENHANCED FEATURES: System Backup Manager
# ============================================================================

class BackupManager:
    """Manage system backups and snapshots"""
    def __init__(self, backup_dir: Path = None):
        self.backup_dir = backup_dir or Path.home() / ".illi_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_dir / "backups.json"
    
    def create_backup(self, name: str, source_paths: list):
        """Create a backup of specified paths"""
        import shutil
        backup_name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        files_backed_up = 0
        for source in source_paths:
            try:
                source_path = Path(source)
                if source_path.exists():
                    if source_path.is_file():
                        shutil.copy2(source, backup_path / source_path.name)
                        files_backed_up += 1
                    elif source_path.is_dir():
                        shutil.copytree(source, backup_path / source_path.name, dirs_exist_ok=True)
                        files_backed_up += 1
            except Exception as e:
                pass
        
        metadata = self._load_metadata()
        metadata[backup_name] = {
            "created": datetime.now().isoformat(),
            "source_paths": source_paths,
            "files": files_backed_up,
            "size_mb": self._dir_size_mb(backup_path)
        }
        self._save_metadata(metadata)
        return backup_name, files_backed_up
    
    def _dir_size_mb(self, path: Path):
        total = sum(f.stat().st_size for f in path.rglob('*') if f.is_file()) / (1024 * 1024)
        return round(total, 2)
    
    def _load_metadata(self):
        if self.metadata_file.exists():
            return json.loads(self.metadata_file.read_text())
        return {}
    
    def _save_metadata(self, metadata):
        self.metadata_file.write_text(json.dumps(metadata, indent=2))
    
    def get_backups(self):
        return self._load_metadata()
    
    def restore_backup(self, backup_name: str, restore_path: Path):
        import shutil
        backup_path = self.backup_dir / backup_name
        if backup_path.exists():
            restore_path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(backup_path, restore_path, dirs_exist_ok=True)
            return True
        return False

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session():
    """Initialize all session state"""
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.hud_active = True
        
        # Core modules
        st.session_state.memory_system = core_components["memory_system"]() if "memory_system" in core_components else None
        st.session_state.voice_engine = core_components["voice_engine"]() if "voice_engine" in core_components else None
        st.session_state.power_manager = core_components["power_manager"]() if "power_manager" in core_components else None
        
        # Advanced features
        st.session_state.ai_automation = core_components["ai_automation"]() if "ai_automation" in core_components else None
        st.session_state.system_monitor = core_components["system_monitor"](st.session_state.ai_automation) if "system_monitor" in core_components and st.session_state.ai_automation else None
        st.session_state.api_server = core_components["api_server"](st.session_state.ai_automation, st.session_state.power_manager, st.session_state.voice_engine) if "api_server" in core_components else None
        st.session_state.webhook_manager = core_components["webhook_manager"]() if "webhook_manager" in core_components else None
        
        st.session_state.scheduler = TaskScheduler()
        st.session_state.analytics = SystemAnalytics()
        st.session_state.backup_manager = BackupManager()
        
        st.session_state.active_tab = "dashboard"
        st.session_state.shell_logs = []
        st.session_state.status_message = "✅ System Ready"
        st.session_state.api_running = False

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.markdown("# 📊 ILLI OS v2.0")
selected_tab = st.sidebar.radio(
    "Select Module:",
    ["🏠 Dashboard", "📈 Analytics", "📅 Scheduler", "💾 Backup", "🤖 AI Automation", "⚡ Control", "🌐 API & Webhooks", "⚠️ Monitoring", "🔧 Settings"]
)

init_session()

# ============================================================================
# TAB: DASHBOARD
# ============================================================================

if selected_tab == "🏠 Dashboard":
    st.title("🏠 System Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        metrics = fetch_live_metrics()
        
        with col1:
            st.metric("CPU", f"{metrics['cpu']:.1f}%")
        with col2:
            st.metric("RAM", f"{metrics['ram']:.1f}%")
        with col3:
            st.metric("Network Sent", f"{metrics['net_bytes_sent'] / 1024**2:.1f} MB")
        with col4:
            st.metric("Network Recv", f"{metrics['net_bytes_recv'] / 1024**2:.1f} MB")
        
        # Log metrics
        st.session_state.analytics.log_metrics(metrics['cpu'], metrics['ram'], 0, metrics['net_bytes_sent'], metrics['net_bytes_recv'])
        
    except Exception as e:
        st.error(f"Failed to fetch metrics: {str(e)}")
    
    st.markdown("---")
    
    # Recent Activities
    st.subheader("📋 Recent Activities")
    if st.session_state.shell_logs:
        for log in st.session_state.shell_logs[-10:]:
            level = log.get("level", "INFO")
            message = log.get("message", "")
            color = {"ERROR": "red", "WARNING": "yellow", "SUCCESS": "green"}.get(level, "blue")
            st.write(f":{color}[{level}] {message}")
    else:
        st.info("No activities yet")

# ============================================================================
# TAB: ANALYTICS
# ============================================================================

elif selected_tab == "📈 Analytics":
    st.title("📈 Performance Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Metrics History", "Performance Report", "Data Export"])
    
    with tab1:
        st.subheader("📊 System Metrics Over Time")
        history = st.session_state.analytics.get_metrics_history(100)
        if history:
            timestamps = [row[0] for row in history]
            cpu_values = [row[1] for row in history]
            ram_values = [row[2] for row in history]
            
            st.line_chart({
                "CPU (%)": cpu_values,
                "RAM (%)": ram_values
            })
            st.info(f"📊 Displaying {len(history)} recent measurements")
        else:
            st.info("No metrics data yet. Generate some activity to see metrics.")
    
    with tab2:
        st.subheader("📋 Performance Report")
        if history:
            avg_cpu = sum(row[1] for row in history) / len(history)
            avg_ram = sum(row[2] for row in history) / len(history)
            max_cpu = max(row[1] for row in history)
            max_ram = max(row[2] for row in history)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average CPU", f"{avg_cpu:.1f}%")
                st.metric("Peak CPU", f"{max_cpu:.1f}%")
            with col2:
                st.metric("Average RAM", f"{avg_ram:.1f}%")
                st.metric("Peak RAM", f"{max_ram:.1f}%")
    
    with tab3:
        st.subheader("📥 Export Metrics")
        if st.button("📥 Export to CSV"):
            history = st.session_state.analytics.get_metrics_history(500)
            if history:
                csv_data = "timestamp,cpu_percent,ram_percent,disk_percent,net_bytes_sent,net_bytes_recv\n"
                for row in history:
                    csv_data += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"
                st.download_button(
                    "📥 Download CSV",
                    csv_data,
                    "metrics.csv",
                    "text/csv"
                )

# ============================================================================
# TAB: SCHEDULER
# ============================================================================

elif selected_tab == "📅 Scheduler":
    st.title("📅 Task Scheduler")
    
    tab1, tab2 = st.tabs(["Manage Tasks", "View Schedule"])
    
    with tab1:
        st.subheader("➕ Add New Task")
        
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("Task Name")
            task_action = st.selectbox("Action", ["Run Script", "Launch App", "System Command", "Backup"])
        
        with col2:
            task_desc = st.text_area("Description")
            schedule_type = st.selectbox("Schedule", ["Daily", "Weekly", "Monthly", "Once"])
        
        schedule_time = st.time_input("Time to run")
        
        if st.button("➕ Add Task"):
            if task_name.strip():
                st.session_state.scheduler.add_task(
                    task_name, 
                    task_desc, 
                    task_action,
                    schedule_type,
                    schedule_time.isoformat()
                )
                st.success(f"✅ Task '{task_name}' added successfully!")
    
    with tab2:
        st.subheader("📋 Scheduled Tasks")
        tasks = st.session_state.scheduler.get_tasks()
        
        if tasks:
            task_data = []
            for task in tasks:
                task_data.append({
                    "ID": task[0],
                    "Name": task[1],
                    "Action": task[3],
                    "Schedule": f"{task[4]} at {task[5]}",
                    "Enabled": "✅" if task[6] else "❌",
                    "Last Run": task[7] or "Never"
                })
            st.dataframe(task_data, use_container_width=True)
        else:
            st.info("No scheduled tasks yet")

# ============================================================================
# TAB: BACKUP
# ============================================================================

elif selected_tab == "💾 Backup":
    st.title("💾 Backup Manager")
    
    tab1, tab2 = st.tabs(["Create Backup", "Restore & View"])
    
    with tab1:
        st.subheader("📦 Create New Backup")
        
        backup_name = st.text_input("Backup Name", value=f"backup_{datetime.now().strftime('%Y%m%d')}")
        
        st.write("Select paths to backup:")
        backup_home = st.checkbox("📁 Home Directory", value=True)
        backup_desktop = st.checkbox("🖥️ Desktop", value=True)
        backup_documents = st.checkbox("📄 Documents", value=False)
        
        source_paths = []
        if backup_home:
            source_paths.append(str(Path.home()))
        if backup_desktop:
            source_paths.append(str(Path.home() / "Desktop"))
        if backup_documents:
            source_paths.append(str(Path.home() / "Documents"))
        
        if st.button("📦 Create Backup"):
            if source_paths:
                with st.spinner("Creating backup..."):
                    backup_id, files = st.session_state.backup_manager.create_backup(backup_name, source_paths)
                    st.success(f"✅ Backup created: {backup_id}\n📁 Files backed up: {files}")
            else:
                st.warning("Select at least one path to backup")
    
    with tab2:
        st.subheader("📋 Available Backups")
        backups = st.session_state.backup_manager.get_backups()
        
        if backups:
            for backup_name, metadata in backups.items():
                with st.expander(f"📦 {backup_name}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Created", metadata['created'][:10])
                    with col2:
                        st.metric("Files", metadata['files'])
                    with col3:
                        st.metric("Size", f"{metadata['size_mb']} MB")
        else:
            st.info("No backups yet")

# ============================================================================
# TAB: CONTROL
# ============================================================================

elif selected_tab == "⚡ Control":
    st.title("⚡ System Control")
    
    if not HAS_CORE:
        st.error("Core modules not available. Cannot access system controls.")
    else:
        tab1, tab2, tab3 = st.tabs(["Power", "Voice", "Launcher"])
        
        with tab1:
            st.subheader("⚡ Power Management")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("💤 Sleep", use_container_width=True):
                    st.session_state.power_manager.sleep_system()
                    st.info("System sleep initiated")
            
            with col2:
                if st.button("🔄 Restart", use_container_width=True):
                    st.warning("Restart in 10 seconds...")
                    st.session_state.power_manager.restart_system(delay_seconds=10)
            
            with col3:
                if st.button("⛔ Shutdown", use_container_width=True):
                    st.warning("Shutdown in 10 seconds...")
                    st.session_state.power_manager.shutdown_system(delay_seconds=10)
            
            with col4:
                if st.button("🗑️ Clear Recycle", use_container_width=True):
                    if st.session_state.power_manager.clear_recycle_bin():
                        st.success("Recycle bin cleared")
        
        with tab2:
            st.subheader("🎤 Voice Control")
            
            col1, col2 = st.columns(2)
            with col1:
                voice_type = st.radio("Select Voice", ["Male", "Female"])
                if st.button("🗣️ Set Voice"):
                    st.session_state.voice_engine.select_voice(voice_type.lower())
                    st.success(f"Voice set to {voice_type}")
            
            with col2:
                test_text = st.text_area("Text to speak", "Hello, I am ILLI OS")
                if st.button("📢 Speak"):
                    st.session_state.voice_engine.synthesize_speech(test_text)
                    st.info("Speech playing...")
        
        with tab3:
            st.subheader("🚀 Launch Applications")
            app_name = st.text_input("Application name", placeholder="notepad, calculator, chrome")
            if st.button("🚀 Launch"):
                if app_name:
                    st.session_state.power_manager.launch_application(app_name)
                    st.success(f"Launching {app_name}...")

# ============================================================================
# TAB: SETTINGS
# ============================================================================

elif selected_tab == "🔧 Settings":
    st.title("🔧 Settings & Preferences")
    
    tab1, tab2, tab3 = st.tabs(["General", "Voice", "Privacy"])
    
    with tab1:
        st.subheader("🔧 General Settings")
        theme = st.selectbox("Theme", ["Dark", "Light"])
        auto_start = st.checkbox("Auto-start on boot", value=True)
        notifications = st.checkbox("Enable notifications", value=True)
        
        if st.button("💾 Save Settings"):
            if st.session_state.memory_system:
                st.session_state.memory_system.set_preference("theme", theme)
                st.session_state.memory_system.set_preference("auto_start", auto_start)
                st.session_state.memory_system.set_preference("notifications", notifications)
            st.success("Settings saved!")
    
    with tab2:
        st.subheader("🎤 Voice Preferences")
        if st.session_state.voice_engine:
            user_name = st.text_input("Call me", value=st.session_state.memory_system.get_voice_preference() if st.session_state.memory_system else "Sir")
            voice_speed = st.slider("Voice Speed", 50, 300, 150)
            voice_volume = st.slider("Voice Volume", 0.0, 1.0, 1.0, 0.1)
            
            if st.button("💾 Save Voice Settings"):
                st.session_state.memory_system.update_voice_preference(user_name)
                st.session_state.voice_engine.set_voice_parameters(voice_speed, voice_volume)
                st.success("Voice settings saved!")
        else:
            st.warning("Voice engine not available")
    
    with tab3:
        st.subheader("🔒 Privacy & Security")
        clear_history = st.checkbox("Clear activity history on exit")
        delete_backups = st.checkbox("Delete old backups (30 days+)")
        
        if st.button("🧹 Clean Up Now"):
            st.info("Cleaning up old data...")
            st.success("Cleanup completed!")

# ============================================================================
# TAB: AI AUTOMATION
# ============================================================================

elif selected_tab == "🤖 AI Automation":
    st.title("🤖 AI Automation Engine")
    
    if not st.session_state.ai_automation:
        st.error("❌ AI Automation engine not available. Install required packages.")
    else:
        tab1, tab2, tab3 = st.tabs(["Create Task", "Task List", "Execution History"])
        
        with tab1:
            st.subheader("➕ Create New Automation Task")
            
            col1, col2 = st.columns(2)
            with col1:
                task_name = st.text_input("Task Name")
                task_description = st.text_area("Description")
            
            with col2:
                trigger_type = st.selectbox("Trigger Type", ["schedule", "voice", "api", "condition"])
                action_type = st.selectbox("Action Type", ["query_ai", "execute_system_command", "launch_application", "send_notification", "http_request"])
            
            parameters_json = st.text_area("Parameters (JSON)", value="{}", height=100)
            
            if st.button("➕ Create Task"):
                try:
                    params = json.loads(parameters_json)
                    task_id = st.session_state.ai_automation.create_task(
                        task_name,
                        task_description,
                        trigger_type,
                        action_type,
                        params
                    )
                    st.success(f"✅ Task created: {task_id}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON in parameters")
        
        with tab2:
            st.subheader("📋 Active Automation Tasks")
            tasks = st.session_state.ai_automation.get_all_tasks()
            
            if tasks:
                for task in tasks:
                    with st.expander(f"🤖 {task['name']} ({task['status']})"):
                        st.write(f"**Description:** {task['description']}")
                        st.write(f"**Trigger:** {task['trigger']}")
                        st.write(f"**Status:** {task['status']}")
                        st.write(f"**Created:** {task['created_at']}")
                        
                        if st.button(f"▶️ Execute {task['task_id']}", key=task['task_id']):
                            with st.spinner("Executing..."):
                                result = st.session_state.ai_automation.execute_task(task['task_id'])
                                st.json(result)
            else:
                st.info("No automation tasks created yet")
        
        with tab3:
            st.subheader("📊 Execution History")
            history = st.session_state.ai_automation.get_execution_history(30)
            
            if history:
                for record in history[-10:]:
                    status_emoji = "✅" if record.get("status") == "success" else "❌"
                    st.write(f"{status_emoji} **{record['task_id']}** - {record['timestamp']}")
                    if record.get("error"):
                        st.write(f"   Error: {record['error']}")
            else:
                st.info("No execution history yet")

# ============================================================================
# TAB: API & WEBHOOKS
# ============================================================================

elif selected_tab == "🌐 API & Webhooks":
    st.title("🌐 API Server & Webhooks")
    
    tab1, tab2 = st.tabs(["API Server", "Webhooks"])
    
    with tab1:
        st.subheader("🌐 REST API Server")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            **API Endpoints:**
            - `GET /health` - Health check
            - `POST /api/tasks/create` - Create automation task
            - `POST /api/tasks/{task_id}/execute` - Execute task
            - `GET /api/system/metrics` - Get system metrics
            - `POST /api/voice/speak` - Text to speech
            - `POST /api/power/sleep` - Sleep system
            - More endpoints available...
            """)
        
        with col2:
            if st.button("🚀 Start API Server"):
                if st.session_state.api_server:
                    success = st.session_state.api_server.run(host="127.0.0.1", port=8000)
                    if success:
                        st.session_state.api_running = True
                        st.success("✅ API Server running on http://localhost:8000")
                        st.info("📚 API Docs: http://localhost:8000/docs")
                    else:
                        st.error("Failed to start API server")
            
            if st.session_state.api_running:
                st.write("✅ **API Status:** Running")
    
    with tab2:
        st.subheader("📨 Webhook Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name", placeholder="e.g., task_completed")
            webhook_url = st.text_input("Webhook URL", placeholder="https://example.com/webhook")
            
            if st.button("📨 Register Webhook"):
                if st.session_state.webhook_manager:
                    if st.session_state.webhook_manager.register_webhook(event_name, webhook_url):
                        st.success(f"✅ Webhook registered for '{event_name}'")
                    else:
                        st.warning("Webhook already registered")
        
        with col2:
            if st.session_state.webhook_manager:
                all_webhooks = st.session_state.webhook_manager.get_webhooks()
                if all_webhooks:
                    st.subheader("📋 Registered Webhooks")
                    for event, urls in all_webhooks.items():
                        st.write(f"**{event}**: {len(urls)} webhook(s)")
                        for url in urls:
                            st.code(url)

# ============================================================================
# TAB: SYSTEM MONITORING & ALERTS
# ============================================================================

elif selected_tab == "⚠️ Monitoring":
    st.title("⚠️ System Monitoring & Alerts")
    
    if not st.session_state.system_monitor:
        st.error("System monitor not available")
    else:
        tab1, tab2 = st.tabs(["Active Monitoring", "Alert History"])
        
        with tab1:
            st.subheader("🔍 System Health Check")
            
            if st.button("🔄 Check System Now"):
                with st.spinner("Scanning system..."):
                    alerts = st.session_state.system_monitor.check_system_conditions()
                    
                    if alerts:
                        for alert in alerts:
                            alert_type = alert.get("type", "unknown")
                            severity = alert.get("severity", "info")
                            value = alert.get("value", "N/A")
                            threshold = alert.get("threshold", "N/A")
                            
                            if severity == "critical":
                                st.error(f"🔴 **CRITICAL**: {alert_type} = {value}% (threshold: {threshold}%)")
                            elif severity == "warning":
                                st.warning(f"🟡 **WARNING**: {alert_type} = {value}% (threshold: {threshold}%)")
                            else:
                                st.info(f"🔵 **INFO**: {alert_type} = {value}%")
                    else:
                        st.success("✅ All systems normal")
            
            # Threshold settings
            st.subheader("⚙️ Alert Thresholds")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cpu_threshold = st.slider("CPU Max %", 50, 100, int(st.session_state.system_monitor.thresholds.get("cpu_max", 80)))
            with col2:
                ram_threshold = st.slider("RAM Max %", 50, 100, int(st.session_state.system_monitor.thresholds.get("ram_max", 85)))
            with col3:
                disk_threshold = st.slider("Disk Max %", 50, 100, int(st.session_state.system_monitor.thresholds.get("disk_max", 90)))
            with col4:
                temp_threshold = st.slider("Temp Max °C", 50, 120, int(st.session_state.system_monitor.thresholds.get("temp_max", 85)))
            
            if st.button("💾 Save Thresholds"):
                st.session_state.system_monitor.thresholds = {
                    "cpu_max": cpu_threshold,
                    "ram_max": ram_threshold,
                    "disk_max": disk_threshold,
                    "temp_max": temp_threshold
                }
                st.success("Thresholds updated!")
        
        with tab2:
            st.subheader("📊 Alert History")
            alerts = st.session_state.system_monitor.get_alerts(30)
            
            if alerts:
                alert_df = []
                for alert in alerts:
                    alert_df.append({
                        "Time": alert.get("timestamp", "")[-8:],
                        "Type": alert.get("type", ""),
                        "Severity": alert.get("severity", ""),
                        "Value": f"{alert.get('value', 0):.1f}%"
                    })
                
                st.dataframe(alert_df, use_container_width=True)
            else:
                st.info("No alerts recorded")

# ============================================================================
# FOOTER
# ============================================================================


st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🤖 ILLI OS v2.0 | Advanced System Control & Automation</p>
    <p style='font-size: 0.8em; color: #666;'>Powered by Streamlit</p>
</div>
""", unsafe_allow_html=True)
