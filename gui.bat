if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] venv folder not found!
    echo Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo =============================================
echo     Profanity Muter - GUI MODE
echo =============================================
echo.
python mute_profanity_gui.py
EOF