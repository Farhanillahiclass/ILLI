@echo off
REM Start ILLI OS v2.0 Enhanced HUD

cd /d G:\illi0001
echo Starting ILLI OS v2.0 Enhanced HUD...
echo.
echo Using virtual environment: .venv_new
echo.

call .\.venv_new\Scripts\activate.bat

echo Virtual environment activated.
echo.
echo Starting Streamlit app...
echo Open your browser at: http://localhost:8501
echo.

streamlit run app_enhanced.py --logger.level=warning

pause
