@echo off
setlocal enabledelayedexpansion
title Limited Tender Manager -- Server Running
color 2F
cls

echo.
echo  ================================================================
echo    LIMITED TENDER MANAGER v2.0 -- Starting Server...
echo  ================================================================
echo.

:: Find Python
set PY=
for %%p in (
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
) do (
    if exist %%p set PY=%%p & goto py_ok
)
where python >nul 2>&1
if %errorlevel% equ 0 (set PY=python & goto py_ok)

color 4F
echo  ERROR: Python not found. Please run SETUP.bat first.
pause & exit /b 1

:py_ok
echo  Keep this window OPEN while the server is running.
echo  Press Ctrl+C to stop.
echo.
echo  ================================================================
echo.
cd /d "%~dp0"
%PY% app.py

echo.
echo  Server stopped.
pause
