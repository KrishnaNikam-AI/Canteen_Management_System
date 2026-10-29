@echo off
setlocal

:: ==============================================================================
:: Canteen Management System - Web Application Launcher Batch Script
:: ==============================================================================
title Canteen Management System - Web App Runner
cd /d "%~dp0"

echo ==============================================================================
echo              CANTEEN MANAGEMENT SYSTEM - WEB APPLICATION RUNNER               
echo ==============================================================================
echo.

:: 1. Check if Python is installed and accessible in PATH
where python >nul 2>&1
if errorlevel 1 goto PYTHON_NOT_FOUND

:: 2. Check and activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" goto ACTIVATE_VENV
if exist ".venv\Scripts\activate.bat" goto ACTIVATE_DOT_VENV

echo [NOTE] No virtual environment folder found. Running with system Python.
echo        To create one: python -m venv venv
echo.
goto ENV_CHECK

:ACTIVATE_VENV
echo [INFO] Activating virtual environment: venv
call "venv\Scripts\activate.bat"
goto ENV_CHECK

:ACTIVATE_DOT_VENV
echo [INFO] Activating virtual environment: .venv
call ".venv\Scripts\activate.bat"
goto ENV_CHECK

:ENV_CHECK
:: 3. Check for .env file; create from .env.example if missing
if exist ".env" goto DEP_CHECK
if exist ".env.example" (
    echo [INFO] No .env file found. Copying .env.example to .env...
    copy ".env.example" ".env" >nul
    echo [ACTION REQUIRED] A new .env file was created!
    echo                   Please open .env in Notepad and set your DB_PASSWORD.
    echo.
)

:DEP_CHECK
:: 4. Verify that core dependencies are installed
echo [INFO] Checking Python dependencies...
python -c "import mysql.connector, dotenv, flask, flask_cors" >nul 2>&1
if errorlevel 1 goto MISSING_DEPS

:: 5. Launch the application
echo [INFO] Starting Web Server at http://127.0.0.1:5000...
echo [INFO] Press Ctrl+C in this terminal window to stop the server.
echo.
python main.py

if errorlevel 1 goto APP_ERROR
goto SCRIPT_END

:PYTHON_NOT_FOUND
echo [ERROR] Python is not installed or not added to your system PATH!
echo Please install Python 3.10+ from https://www.python.org/
echo Make sure to check the box "Add python.exe to PATH" during installation.
echo.
pause
exit /b 1

:MISSING_DEPS
echo.
echo ==============================================================================
echo [ERROR] Missing required Python packages!
echo ==============================================================================
echo Core libraries such as mysql-connector-python, flask, or flask-cors are missing.
echo.
echo To install all required dependencies, run:
echo     pip install -r requirements.txt
echo.
echo ==============================================================================
pause
exit /b 1

:APP_ERROR
echo.
echo [WARNING] Application closed with exit code %errorlevel%.
pause
exit /b %errorlevel%

:SCRIPT_END
endlocal
