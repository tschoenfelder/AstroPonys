@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Run "%~dp0setup.cmd" first. 1>&2
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -m astroponys.raw_qa_worker %*
exit /b %errorlevel%
