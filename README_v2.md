# 🚀 ILLI OS v2.0 - Advanced System Control & Automation Platform

**A powerful, AI-driven system automation and control platform for Windows with REST API, voice automation, and intelligent task execution.**

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Key Features

### 🎯 **Core Control**
- ⚡ System power management (Sleep, Restart, Shutdown)
- 🎤 Advanced TTS/STT with dual-voice synthesis
- 🎨 Wallpaper generation and management
- 🎮 Global hotkey listener
- 🗑️ Safe deletion with confirmation handshakes

### 📊 **Analytics & Monitoring**
- Real-time CPU, RAM, Network metrics
- Performance trend tracking with charts
- Historical data analysis
- CSV export capabilities
- System health alerts with configurable thresholds

### 📅 **Advanced Scheduling**
- Create recurring tasks (Daily, Weekly, Monthly, Once)
- Task execution tracking
- Persistent task storage
- Enable/disable individual tasks

### 💾 **Backup & Recovery**
- One-click backup creation
- Multiple backup destinations
- Automatic metadata tracking
- One-click restore functionality
- Backup history management

### 🤖 **AI Automation Engine**
- Natural language command processing
- Intent classification using transformers
- Intelligent task execution
- System command automation
- HTTP API integration
- Execution history logging

### 🌐 **REST API Server**
- FastAPI-based REST endpoints
- Task creation and execution via API
- System control endpoints
- Voice synthesis endpoints
- Real-time system metrics
- Swagger UI documentation

### 📨 **Webhook Management**
- Event-driven automation
- Register webhooks for automation events
- Trigger external systems
- Integration with third-party services

### ⚠️ **System Monitoring**
- Real-time system health monitoring
- Configurable alert thresholds
- Alert history tracking
- CPU, RAM, and Disk monitoring
- Automatic alert generation

### 🎤 **Voice Automation**
- Voice command processing
- Natural language intent parsing
- Speech-to-text recognition
- Text-to-speech synthesis
- Voice-based task execution

---

## 🚀 Quick Start

### Prerequisites
- Windows 10+
- Python 3.10+
- Git (for repository setup)

### Installation

#### Option 1: Using Batch Script
```bash
# Navigate to project directory
cd G:\illi0001

# Run the batch script
RUN_APP.bat
```

#### Option 2: Manual Setup
```powershell
# Create virtual environment
python -m venv .venv_new

# Activate it
.\.venv_new\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app_enhanced.py
```

### Access the Application
- **Streamlit UI**: http://localhost:8501
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (when API is running)

---

## 📋 Tab Overview

### 🏠 Dashboard
- System overview with live metrics
- Recent activities feed
- Quick status indicators

### 📈 Analytics
- Performance metrics visualization
- Historical trend analysis
- CSV export for external analysis

### 📅 Scheduler
- Create and manage automation tasks
- View execution schedule
- Task status tracking

### 💾 Backup
- Create system backups
- View backup history
- One-click restore

### 🤖 AI Automation
- Create AI-powered automation tasks
- Define custom triggers and actions
- Monitor task execution history
- Execute tasks manually or automatically

### ⚡ Control
- System power management
- Voice control (Male/Female selection)
- Application launcher
- System diagnostics

### 🌐 API & Webhooks
- Start REST API server
- Register event webhooks
- Monitor API endpoint usage
- External system integration

### ⚠️ Monitoring
- System health checks
- Configurable alert thresholds
- Alert history tracking
- Real-time system status

### 🔧 Settings
- User preferences
- Voice customization
- Privacy controls
- Theme selection

---

## 🌐 API Endpoints

### Health & Info
- `GET /health` - Service health check
- `GET /api/system/metrics` - Current system metrics

### Automation Tasks
- `POST /api/tasks/create` - Create new automation task
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/{task_id}` - Get task status
- `POST /api/tasks/{task_id}/execute` - Execute specific task
- `GET /api/execution-history` - Get execution history

### Natural Language Processing
- `POST /api/nlp/parse` - Parse natural language command

### Power Control
- `POST /api/power/sleep` - Sleep system
- `POST /api/power/restart` - Restart system
- `POST /api/power/shutdown` - Shutdown system

### Voice Control
- `POST /api/voice/speak` - Text to speech
- `GET /api/voice/status` - Voice engine status

### Webhooks
- `POST /webhooks/register` - Register event webhook
- `GET /webhooks` - List registered webhooks

---

## 📦 Dependencies

### Core
- `streamlit>=1.28.0` - UI Framework
- `pyttsx3>=2.90` - Text-to-Speech
- `SpeechRecognition>=3.10.0` - Speech-to-Text

### AI & Automation
- `transformers>=4.35.0` - NLP Models
- `torch>=2.1.0` - Deep Learning Framework
- `apscheduler>=3.10.0` - Task Scheduling

### System Control
- `pycaw>=20190726` - Audio Control
- `pynput>=1.7.6` - Hotkeys
- `pyautogui>=0.9.54` - GUI Automation
- `keyboard>=0.13.5` - Keyboard Control
- `mouse>=0.7.1` - Mouse Control

### API & Web
- `fastapi>=0.104.0` - REST Framework
- `uvicorn>=0.24.0` - ASGI Server
- `websockets>=12.0` - WebSocket Support

### Database & Storage
- `sqlalchemy>=2.0.0` - ORM
- `psutil>=5.9.0` - System Monitoring

---

## 🎯 Usage Examples

### Create an Automation Task via API
```bash
curl -X POST http://localhost:8000/api/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Backup",
    "description": "Backup important files daily",
    "trigger": "schedule",
    "action": "execute_system_command",
    "parameters": {
      "command": "robocopy C:\\Users\\Documents D:\\Backups /E"
    }
  }'
```

### Parse Natural Language Command
```bash
curl -X POST http://localhost:8000/api/nlp/parse \
  -H "Content-Type: application/json" \
  -d '{"command": "Launch Notepad and create a new file"}'
```

### Get System Metrics
```bash
curl http://localhost:8000/api/system/metrics
```

### Text to Speech
```bash
curl -X POST http://localhost:8000/api/voice/speak \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is ILLI OS",
    "voice_type": "male"
  }'
```

---

## 🗂️ Project Structure

```
G:\illi0001\
├── app.py                      # Original Streamlit app
├── app_enhanced.py             # Enhanced HUD with all features
├── RUN_APP.bat                 # Windows launcher script
├── SETUP_GUIDE.md              # Setup documentation
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── illi/
│   ├── __init__.py
│   ├── core.py                 # Voice synthesis & memory system
│   ├── automation.py           # Power management
│   ├── interface.py            # UI components
│   ├── hotkeys.py              # Global hotkey listener
│   ├── power.py                # System power control
│   ├── wallpaper.py            # Wallpaper generation
│   ├── ai_automation.py        # AI task automation engine
│   ├── api_server.py           # FastAPI REST server
│   ├── voice_automation.py     # Voice command processing
│   └── cli.py                  # Command-line interface
├── .venv_new/                  # Python virtual environment
├── data/                       # Data storage
├── logs/                       # Application logs
└── .gitignore
```

---

## 🔧 Advanced Configuration

### Memory System
The app uses SQLite for persistent storage:
```
~/.illi_memory/cognition.db     # User preferences & history
~/.illi_scheduler/tasks.db      # Scheduled tasks
~/.illi_analytics/metrics.db    # Performance metrics
~/.illi_backups/                # Backup storage
```

### Logging
Configure logging level in environment:
```powershell
$env:LOGLEVEL = "DEBUG"  # DEBUG, INFO, WARNING, ERROR
streamlit run app_enhanced.py
```

---

## 🐛 Troubleshooting

### Port Already in Use
```powershell
# Kill process on port 8501 (Streamlit)
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Use different port
streamlit run app_enhanced.py --server.port=8502
```

### Audio/TTS Not Working
- Ensure speakers are enabled
- Check System > Sound settings
- Install Windows media packs if needed

### API Server Won't Start
- Ensure port 8000 is available
- Check firewall settings
- Install FastAPI/Uvicorn: `pip install fastapi uvicorn`

### Import Errors
```powershell
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Performance Tips

1. **Reduce Metrics Collection**: Adjust analytics sample rate
2. **Disable Unused Features**: Skip unnecessary modules at startup
3. **Optimize Backups**: Use incremental backups for large datasets
4. **API Performance**: Use webhooks instead of polling
5. **Voice Processing**: Use faster speech recognition models

---

## 🔐 Security Notes

- ⚠️ API server runs on localhost by default (not externally accessible)
- 🔒 All automation tasks are logged
- 🛡️ Deletion protection requires manual confirmation
- 🔑 Store sensitive data in environment variables, not code

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support & Issues

- 📖 Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation help
- 🐛 Report bugs via GitHub Issues
- 💬 Discussions for questions and feedback

---

## 🚀 Roadmap

- [ ] Machine learning model for predictive automation
- [ ] Mobile app for remote control
- [ ] Cloud sync for preferences
- [ ] Advanced analytics dashboard
- [ ] Plugin system for custom integrations
- [ ] Distributed task execution
- [ ] Multi-user support

---

## 👤 Author

**Muhammad Anas**
- 🌐 GitHub: [Profile](https://github.com/your-username)
- 📧 Email: your-email@example.com

---

**ILLI OS v2.0** | Advanced System Control & Automation  
*Making system automation intelligent, accessible, and powerful.*

Last Updated: May 29, 2026
