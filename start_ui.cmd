@echo off
cd /d "%~dp0"
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ui.py %*
    goto :eof
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -B ui.py %*
    goto :eof
)
python -B ui.py %*
if errorlevel 1 pause
