# ILLI Installation Guide

## System Requirements

- **OS**: Windows 10/11 (Primary), Linux (Coming Soon)
- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **RAM**: 16GB+ (32GB recommended)
- **Storage**: 50GB+ SSD space
- **GPU**: NVIDIA GPU with CUDA support (Recommended)

## Quick Install

### Windows

1. **Clone the repository**
```bash
git clone https://github.com/Farhanillahiclass/ILLI.git
cd ILLI
```

2. **Run the installation script**
```bash
python scripts/install.py
```

3. **Start ILLI**
```bash
python -m illi.cli start
```

4. **Start the dashboard** (in a new terminal)
```bash
cd dashboard
npm run dev
```

### Manual Installation

If the automated script fails, you can install manually:

#### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Install Node.js Dependencies

```bash
cd dashboard
npm install
cd ..
```

#### 3. Create Directories

```bash
mkdir -p data/memory data/chroma data/workflows logs snapshots models backups config/security config/plugin_registry
```

#### 4. Initialize System

```bash
python -m scripts.init
```

#### 5. Download a Model (Optional)

Using Ollama:
```bash
ollama pull llama2
```

Or download GGUF models manually and place in `models/` directory.

## Optional Components

### GPU Support

For GPU acceleration, install CUDA and cuDNN:

1. Install NVIDIA drivers
2. Install CUDA Toolkit
3. Install cuDNN
4. Install PyTorch with CUDA support:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Voice Support

For voice features, install additional dependencies:

```bash
pip install openai-whisper pyttsx3 pyaudio
```

Note: On Windows, you may need to install Microsoft Visual C++ Redistributable.

### Vision Support

For vision features, install additional dependencies:

```bash
pip install opencv-python pytesseract easyocr ultralytics
```

Download Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki

### Computer Control

For computer control features:

```bash
pip install pyautogui pywinauto keyboard mouse
```

## Configuration

Edit `config/engine_config.json` to customize:

- Model settings
- Memory configuration
- Agent settings
- System parameters

## Troubleshooting

### Python Version Error

Ensure you have Python 3.10+:
```bash
python --version
```

### GPU Not Detected

1. Verify NVIDIA drivers are installed
2. Check CUDA installation
3. Test PyTorch CUDA:
```python
import torch
print(torch.cuda.is_available())
```

### Port Already in Use

Change the dashboard port in `config/system_config.json` or use:
```bash
npm run dev -- -p 3001
```

### Memory Errors

Reduce context size in `config/engine_config.json` or use a smaller model.

## Uninstallation

To remove ILLI:

1. Stop all running instances
2. Delete the repository directory
3. Remove configuration files from `config/`
4. Remove data files from `data/`

## Updates

To update ILLI:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
cd dashboard
npm install
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/Farhanillahiclass/ILLI/issues
- Documentation: See README.md
