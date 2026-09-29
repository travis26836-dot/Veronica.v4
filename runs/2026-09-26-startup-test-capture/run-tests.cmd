@echo off
cd /d "%~dp0\..\.."
uv run pytest tests\test_start_veronica.py -q > "%~dp0combined.txt" 2>&1
echo %ERRORLEVEL% > "%~dp0exit.txt"
exit /b %ERRORLEVEL%
