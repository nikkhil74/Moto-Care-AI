@echo off
title MotoCare AI - Web Interface Launcher
echo ========================================================
echo         MotoCare AI - Predictive Engine Maintenance
echo               Starting Web Telemetry Server
echo ========================================================
echo.

cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\india\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PYTHON_EXE%" (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo [ERROR] Python not found. Please install Python 3.11+.
        pause
        exit /b 1
    )
)

echo Starting Flask server at http://127.0.0.1:5000...
echo Opening browser in 2 seconds...

start "" "http://127.0.0.1:5000"

"%PYTHON_EXE%" app.py

pause
