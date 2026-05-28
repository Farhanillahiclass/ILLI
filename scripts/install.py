"""
ILLI Installation Script
Handles system installation and dependency management.
"""

import sys
import subprocess
from pathlib import Path
import platform
import shutil
from typing import Optional, List
import json

def check_python_version() -> bool:
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"Error: Python 3.10+ required, found {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_gpu() -> dict:
    """Check for GPU availability"""
    gpu_info = {
        "has_gpu": False,
        "gpu_type": None,
        "cuda_available": False
    }
    
    try:
        import torch
        gpu_info["cuda_available"] = torch.cuda.is_available()
        if gpu_info["cuda_available"]:
            gpu_info["has_gpu"] = True
            gpu_info["gpu_type"] = "NVIDIA CUDA"
            gpu_info["gpu_count"] = torch.cuda.device_count()
            print(f"✓ GPU detected: {gpu_info['gpu_type']} ({gpu_info['gpu_count']} device(s))")
        else:
            print("⚠ No CUDA GPU detected (CPU mode)")
    except ImportError:
        print("⚠ PyTorch not installed, skipping GPU check")
    
    return gpu_info

def install_python_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing Python dependencies: {e}")
        return False

def install_node_dependencies():
    """Install Node.js dependencies"""
    print("\nInstalling Node.js dependencies...")
    
    # Check if npm is available
    try:
        subprocess.check_call(["npm", "--version"], stdout=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ npm not found. Please install Node.js from https://nodejs.org/")
        return False
    
    try:
        subprocess.check_call(["npm", "install"], cwd="dashboard")
        print("✓ Node.js dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing Node.js dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    directories = [
        "data/memory",
        "data/chroma",
        "data/workflows",
        "logs",
        "snapshots",
        "models",
        "backups",
        "config/security",
        "config/plugin_registry"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created")

def download_model(model_name: str = "llama2"):
    """Download a default model using Ollama"""
    print(f"\nDownloading model: {model_name}...")
    
    try:
        # Check if ollama is available
        subprocess.check_call(["ollama", "--version"], stdout=subprocess.DEVNULL)
        
        subprocess.check_call(["ollama", "pull", model_name])
        print(f"✓ Model {model_name} downloaded")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Ollama not found. Please install from https://ollama.ai/")
        print("  You can download models later using: ollama pull <model>")
        return False

def create_config():
    """Create configuration files"""
    print("\nCreating configuration files...")
    
    config = {
        "system": {
            "log_level": "INFO",
            "max_concurrent_tasks": 10,
            "task_timeout": 300
        },
        "model": {
            "default_model": "llama2",
            "context_size": 4096,
            "temperature": 0.7
        },
        "dashboard": {
            "port": 3000,
            "host": "localhost"
        }
    }
    
    config_file = Path("config/system_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Configuration created")

def create_desktop_shortcut():
    """Create desktop shortcut (Windows only)"""
    if platform.system() != "Windows":
        return
    
    print("\nCreating desktop shortcut...")
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "ILLI.lnk")
        target = sys.executable
        wDir = os.getcwd()
        icon = os.path.join(wDir, "illi.ico")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Arguments = "-m illi.cli start"
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon if os.path.exists(icon) else target
        shortcut.save()
        
        print("✓ Desktop shortcut created")
    except ImportError:
        print("⚠ Could not create desktop shortcut (pywin32 required)")
    except Exception as e:
        print(f"⚠ Could not create desktop shortcut: {e}")

def run_initialization():
    """Run system initialization"""
    print("\nRunning system initialization...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "scripts.init"
        ])
        print("✓ System initialized")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error during initialization: {e}")
        return False
    
    return True

def main():
    """Main installation function"""
    print("=" * 60)
    print("ILLI Installation")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check system
    print(f"\nSystem: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    
    # Check GPU
    gpu_info = check_gpu()
    
    # Create directories
    create_directories()
    
    # Install dependencies
    python_ok = install_python_dependencies()
    node_ok = install_node_dependencies()
    
    if not python_ok:
        print("\n✗ Installation failed: Python dependencies")
        sys.exit(1)
    
    # Create configuration
    create_config()
    
    # Download model (optional)
    download_model()
    
    # Run initialization
    if run_initialization():
        print("\n" + "=" * 60)
        print("✓ Installation completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start ILLI: python -m illi.cli start")
        print("2. Open dashboard: npm run dev (in dashboard directory)")
        print("3. Access dashboard at: http://localhost:3000")
        print("\nFor more information, see README.md")
    else:
        print("\n✗ Installation completed with errors")
        print("You can still try to start ILLI, but some features may not work")

if __name__ == "__main__":
    main()
