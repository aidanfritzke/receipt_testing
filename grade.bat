@echo off
:: Records which items from this morning's practice slip you missed.
cd /d "%~dp0"
py practice_grade.py
echo.
pause
