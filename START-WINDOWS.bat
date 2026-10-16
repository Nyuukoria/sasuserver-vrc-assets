@echo off
setlocal
cd /d "%~dp0"
title Nyuukoria Drive - Local Test
if exist "runtime\python.exe" (
  "runtime\python.exe" "run-local.py"
  goto stopped
)
if exist ".venv\Scripts\python.exe" goto checkdeps
where py >nul 2>&1
if errorlevel 1 (
  echo This source download needs Python 3.12 or newer.
  echo For a completely offline start, use the Nyuukoria-Drive-Offline-Windows ZIP.
  goto stopped
)
py -3 -c "import sys; assert sys.version_info >= (3,12)" >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.12 or newer, or use the complete offline Windows ZIP.
  goto stopped
)
py -3 -m venv .venv
if errorlevel 1 goto stopped
:checkdeps
".venv\Scripts\python.exe" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
  echo Installing dependencies. This first source-only setup needs internet.
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto stopped
)
".venv\Scripts\python.exe" "run-local.py"
:stopped
echo.
echo Nyuukoria Drive has stopped. Your local test files have been kept.
pause
