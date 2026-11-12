@echo off
setlocal
cd /d "%~dp0"
title Tax AI Content Admin

echo ==========================================
echo Tax AI Content Admin
echo Folder: %CD%
echo ==========================================
echo.

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo [ERROR] Python 3 not found.
  echo.
  echo Install Python 3 from https://www.python.org/downloads/
  echo During installation, check "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

echo Using Python:
%PYTHON_CMD% --version
echo.
echo Starting admin server...
echo If a browser does not open automatically, use the URL printed below.
echo.

%PYTHON_CMD% admin\server.py
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
  echo [ERROR] Admin server exited with code %EXITCODE%.
  echo Check the messages above.
)
pause
