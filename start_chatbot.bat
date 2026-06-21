@echo off
title IndiTemp Chatbot Runner
echo ============================================================
echo          Starting India Temperature Chatbot Server
echo ============================================================
echo.
cd /d "%~dp0"
start /b cmd /c "timeout /t 4 >nul && start http://127.0.0.1:8000"
python run.py
pause
