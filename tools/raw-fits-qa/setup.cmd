@echo off
setlocal
pushd "%~dp0" || exit /b 1
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv ".venv" || (popd & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install --only-binary=:all: -r requirements.txt
set "status=%errorlevel%"
popd
exit /b %status%
