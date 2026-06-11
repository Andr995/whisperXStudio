@echo off
setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%.venv-whisperx"
set "PATH=%VENV%\Scripts;%PATH%"

"%VENV%\Scripts\python.exe" "%ROOT%whisperx_frontend.py" --host 127.0.0.1 --port 8765
