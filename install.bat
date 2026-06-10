@echo off
echo Blitztext – Installation
echo ========================
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden. Bitte Python 3.11+ installieren.
    pause
    exit /b 1
)
pip install -r requirements.txt
echo.
echo Fertig. Starten mit: python main.py
pause
