@echo off
title JARVIS 2.0 - 21st.dev Cyber OS
echo ==============================================================================
echo ⚡ Starting JARVIS 2.0 Native Desktop App (21st.dev UI via WebView2)
echo ==============================================================================
python server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application stopped or encountered an error.
    pause
)
