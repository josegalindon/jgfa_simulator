@echo off
echo ========================================
echo  Long-Short Portfolio Simulator
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Checking dependencies...
echo.

REM Check if required packages are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies OK
)

echo.
echo Starting portfolio simulator...
echo Dashboard will be available at: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the Flask application
python app.py

pause
