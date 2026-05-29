# 🚀 ILLI OS v2.0 - Enhanced HUD Setup Guide

## ✅ What's New in v2.0

### 🎨 New Features Added:

1. **📊 Advanced Analytics Dashboard**
   - Real-time system metrics tracking (CPU, RAM, Network)
   - Performance history with charts
   - CSV export for analysis
   - Peak/Average statistics

2. **📅 Task Scheduler**
   - Create recurring tasks (Daily, Weekly, Monthly, Once)
   - Task management interface
   - Schedule view with execution status
   - Persistent task storage

3. **💾 Backup Manager**
   - One-click backup creation
   - Multiple backup destinations
   - Automatic metadata tracking (size, file count, creation time)
   - Restore functionality
   - Backup history management

4. **⚡ Enhanced Control Module**
   - Power management (Sleep, Restart, Shutdown)
   - Voice control (Male/Female selection)
   - Application launcher
   - System command execution

5. **📈 Performance Reporting**
   - Daily/weekly performance summaries
   - Peak usage times
   - Historical trend analysis
   - Data export capabilities

6. **🔧 Advanced Settings Panel**
   - User preferences management
   - Voice customization (speed, volume, gender)
   - Privacy controls
   - Auto-cleanup options
   - Theme selection

---

## 🚀 Quick Start

### Option 1: Using Batch Script (Windows)
```bash
# Double-click the RUN_APP.bat file in G:\illi0001\
# Or run from Command Prompt:
G:\illi0001\RUN_APP.bat
```

### Option 2: Manual Start (PowerShell)
```powershell
# Navigate to project directory
Set-Location G:\illi0001

# Activate virtual environment
.\.venv_new\Scripts\Activate.ps1

# Run the enhanced app
streamlit run app_enhanced.py
```

### Option 3: Run Original App
```powershell
streamlit run app.py
```

---

## 📋 File Structure

```
G:\illi0001\
├── app.py                  # Original Streamlit HUD
├── app_enhanced.py         # NEW: Enhanced HUD with all features
├── RUN_APP.bat             # Windows batch script to start app
├── requirements.txt        # Updated with new packages
├── illi/
│   ├── __init__.py
│   ├── cli.py
│   ├── core.py             # Voice synthesis & memory system
│   ├── automation.py       # Power management
│   ├── interface.py        # UI components
│   ├── hotkeys.py          # Global hotkey listener
│   ├── power.py            # System power control
│   ├── wallpaper.py        # Wallpaper generation
│   └── ...
└── .venv_new/              # Python virtual environment
```

---

## 🎯 Using the Enhanced Features

### Analytics Tab
- View real-time CPU/RAM metrics
- See performance trends over time
- Export metrics to CSV for external analysis
- Generate performance reports

### Scheduler Tab
- Create new scheduled tasks
- Set execution frequency (Daily, Weekly, Monthly, Once)
- View all scheduled tasks with status
- Enable/disable individual tasks

### Backup Tab
- Create backups of important folders
- Select multiple backup destinations
- View backup history with metadata
- One-click restore functionality

### Control Tab
- Power management (sleep, restart, shutdown)
- Voice control with gender selection
- Test voice synthesis
- Launch applications quickly

### Settings Tab
- Customize voice preferences (name, speed, volume)
- Set theme preference
- Configure notification settings
- Privacy controls

---

## 📦 New Dependencies Added

```
streamlit>=1.28.0           # UI Framework
pyttsx3>=2.90               # Text-to-Speech
SpeechRecognition>=3.10.0   # Speech-to-Text
pycaw>=20190726             # Audio Control
pynput>=1.7.6               # Hotkeys
pyautogui>=0.9.54           # GUI Automation
keyboard>=0.13.5            # Keyboard Control
mouse>=0.7.1                # Mouse Control
schedule>=1.2.0             # Task Scheduling
apscheduler>=3.10.0         # Advanced Scheduling
```

---

## 🔧 Troubleshooting

### "Streamlit command not found"
```powershell
# Make sure venv is activated
.\.venv_new\Scripts\Activate.ps1
```

### "Port 8501 already in use"
```powershell
# Kill the process using port 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Or run on different port
streamlit run app_enhanced.py --server.port=8502
```

### Audio/TTS not working
- Install Windows media packs if needed
- Ensure speakers/audio output is configured
- Check System > Sound settings

### Backup fails
- Ensure source paths exist and are accessible
- Check disk space (backups require storage)
- Some system files may be locked

---

## 🌟 Tips & Tricks

1. **Persistent Data**: All preferences, metrics, and tasks are stored locally
2. **Keyboard Shortcuts**: Use Streamlit's built-in shortcuts (Ctrl+M for menu)
3. **Voice Commands**: Can be extended with speech recognition integration
4. **Task Automation**: Combine scheduler with system commands for powerful automation
5. **Export Analytics**: Download CSV and import into Excel/Power BI for advanced analysis

---

## 📞 Support

For issues or feature requests:
1. Check the logs directory for error messages
2. Verify all dependencies are installed: `pip list`
3. Try running with debug: `streamlit run app_enhanced.py --logger.level=debug`

---

**ILLI OS v2.0** | Enhanced System Control & Automation Platform
Last Updated: May 29, 2026
