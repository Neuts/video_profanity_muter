@echo off
echo.
echo =============================================
echo     Profanity Muter - SETUP (Windows)
echo =============================================
echo.

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH!
    echo Please install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

:: Create venv if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    echo ✅ venv created.
) else (
    echo venv already exists.
)

:: Activate venv
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo Installing Python packages...
pip install -r requirements.txt

echo.
echo =============================================
echo SETUP COMPLETE! ✅
echo.
echo To run:
echo   run.bat input.mkv output.mkv
echo   or
echo   run.bat --batch input_folder output_folder
echo.
echo GPU users: If you have NVIDIA CUDA, run this now:
echo   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
echo.
echo Press any key to exit...
pause >nul
EOF