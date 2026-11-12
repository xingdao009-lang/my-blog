@echo off
setlocal
cd /d "%~dp0"
py -3 scripts\update_all.py
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%1"=="--no-pause" pause
