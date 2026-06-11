@echo off
setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%.venv-whisperx"
set "HF_HOME=%ROOT%.cache\huggingface"
set "XDG_CACHE_HOME=%ROOT%.cache"
set "PATH=%VENV%\Scripts;%PATH%"

"%VENV%\Scripts\whisperx.exe" --device cuda --compute_type float16 %*
