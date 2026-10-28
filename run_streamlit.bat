@echo off
title MotoCare AI - Streamlit Launcher
echo ========================================================
echo         MotoCare AI - Streamlit Dashboard Launcher
echo ========================================================
echo.

cd /d "%~dp0"

set "STREAMLIT_EXE=C:\Users\india\AppData\Local\Programs\Python\Python311\Scripts\streamlit.exe"

if not exist "%STREAMLIT_EXE%" (
    where streamlit >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "STREAMLIT_EXE=streamlit"
    ) else (
        echo [ERROR] Streamlit executable not found.
        pause
        exit /b 1
    )
)

echo Starting Streamlit App...
"%STREAMLIT_EXE%" run streamlit_app.py

pause
