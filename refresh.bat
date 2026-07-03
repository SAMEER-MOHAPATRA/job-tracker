@echo off
rem refresh.bat — fetch fresh RSS jobs and regenerate the dashboard
cd /d "%~dp0"
python discover.py --days 3
python dashboard.py
