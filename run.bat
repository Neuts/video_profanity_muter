@echo off
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] venv folder not found!
    echo Run the setup steps from the previous message first.
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo =============================================
echo     Profanity Muter Launcher (venv active)
echo =============================================
python mute_profanity.py %*
EOF