@echo off
setlocal
cd /d "%~dp0"
py -3 scripts\build_articles.py
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%1"=="--no-pause" pause
