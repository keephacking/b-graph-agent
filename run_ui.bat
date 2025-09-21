@echo off
title API Chart Generator - Desktop UI
echo.
echo 🤖 API Chart Generator - Desktop UI
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

REM Launch the UI using Python launcher
python run_ui.py

echo.
echo Press any key to exit...
pause >nul
