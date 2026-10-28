@echo off
title Push MotoCare AI to GitHub (nikkhil74)
echo ========================================================
echo        Pushing MotoCare AI to GitHub
echo        Target: https://github.com/nikkhil74/Moto-Care-AI
echo ========================================================
echo.
cd /d "%~dp0"

git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Project successfully uploaded to https://github.com/nikkhil74/Moto-Care-AI !
) else (
    echo [NOTE] If a browser window opened, complete the login as nikkhil74 and run this again.
)
echo.
pause
