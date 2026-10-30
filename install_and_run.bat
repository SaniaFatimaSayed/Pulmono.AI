@echo off
title Pulmono.AI - Install & Run

echo ==========================================
echo      Pulmono.AI - Install and Run
echo ==========================================
echo.

:: Find a compatible Python version
py -3.11 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=py -3.11
    goto :found
)

py -3.12 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=py -3.12
    goto :found
)

echo.
echo ERROR: Compatible Python version not found.
echo.
echo Pulmono.AI requires Python 3.11 or 3.12.
echo Python 3.14 is currently not supported because some
echo required packages (e.g. numba) do not yet support it.
echo.
echo Please install Python 3.11 or 3.12 from:
echo https://www.python.org/downloads/
echo.
pause
exit /b

:found
echo Using %PYTHON%
echo.

:: Create virtual environment if needed
if not exist ".venv" (
    echo Creating virtual environment...
    %PYTHON% -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate

:: Upgrade pip
python -m pip install --upgrade pip

:: Install dependencies
echo.
echo Installing dependencies, this may take a few minutes...
pip install -r requirements1.txt

if %errorlevel% neq 0 (
    echo.
    echo ==========================================
    echo   ERROR: Failed to install dependencies.
    echo   Check the messages above for details.
    echo ==========================================
    echo.
    pause
    exit /b
)

echo.
echo Dependencies installed successfully.
echo.

:: Launch Streamlit
echo Launching Pulmono.AI...
streamlit run app_v4.py

pause