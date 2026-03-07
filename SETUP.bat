@echo off
setlocal enabledelayedexpansion
title Limited Tender Manager -- Setup
color 1F
cls

echo.
echo  ================================================================
echo    LIMITED TENDER MANAGER v2.0 -- ONE-TIME SETUP
echo  ================================================================
echo.
pause

:: ── FIND PYTHON ──────────────────────────────────────────────────────────────
echo.
echo  [1/3] Checking Python...

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
    if exist %%p set PY=%%p & goto py_found
)
where python >nul 2>&1
if %errorlevel% equ 0 (set PY=python & goto py_found)
where python3 >nul 2>&1
if %errorlevel% equ 0 (set PY=python3 & goto py_found)

color 4F
echo  ERROR: Python not found.
echo  Please install Python from https://www.python.org/downloads/
echo  (tick "Add Python to PATH" during install)
echo  Then run SETUP.bat again.
pause & exit /b 1

:py_found
for /f "tokens=*" %%v in ('%PY% --version 2^>^&1') do echo  %%v found -- OK

:: ── INSTALL PACKAGES ─────────────────────────────────────────────────────────
echo.
echo  [2/3] Installing Python packages...

:: Check if packages folder exists (offline install)
if exist "%~dp0packages\" (
    echo  Found offline packages folder -- installing without internet...
    %PY% -m pip install --no-index --find-links="%~dp0packages" flask flask-cors psycopg2-binary werkzeug
) else (
    echo  No offline packages found.
    echo.
    echo  You need to download packages first on your Mac.
    echo  Run the DOWNLOAD_PACKAGES_ON_MAC.sh script on your Mac,
    echo  then copy the 'packages' folder here next to SETUP.bat.
    echo.
    pause & exit /b 1
)

if %errorlevel% neq 0 (
    color 4F
    echo  ERROR: Package install failed.
    pause & exit /b 1
)
echo  Packages installed -- OK

:: ── FOLDERS ──────────────────────────────────────────────────────────────────
echo.
echo  [3/3] Creating folders and setting up database...
if not exist "%~dp0app\uploads" mkdir "%~dp0app\uploads"

:: ── POSTGRESQL ───────────────────────────────────────────────────────────────
echo.
echo  Setting up PostgreSQL database...
echo  Enter your PostgreSQL password (set during PostgreSQL install).
echo  Press Enter if no password was set.
echo.
set /p PG_PASS=Password for PostgreSQL 'postgres' user: 
set PGPASSWORD=%PG_PASS%

set PSQL=
where psql >nul 2>&1
if %errorlevel% equ 0 (set PSQL=psql & goto psql_found)
for /d %%d in ("%ProgramFiles%\PostgreSQL\*") do (
    if exist "%%d\bin\psql.exe" set PSQL="%%d\bin\psql.exe" & goto psql_found
)

echo.
echo  WARNING: psql not found automatically.
echo  Please open pgAdmin 4 and run these SQL commands manually:
echo.
echo    CREATE DATABASE lt_manager;
echo    CREATE USER lt_user WITH PASSWORD 'lt_password123';
echo    GRANT ALL PRIVILEGES ON DATABASE lt_manager TO lt_user;
echo.
goto db_done

:psql_found
%PSQL% -U postgres -h localhost -c "CREATE DATABASE lt_manager;"        >nul 2>&1
%PSQL% -U postgres -h localhost -c "CREATE USER lt_user WITH PASSWORD 'lt_password123';" >nul 2>&1
%PSQL% -U postgres -h localhost -c "GRANT ALL PRIVILEGES ON DATABASE lt_manager TO lt_user;" >nul 2>&1
%PSQL% -U postgres -h localhost -d lt_manager -c "GRANT ALL ON SCHEMA public TO lt_user;" >nul 2>&1
echo  Database setup -- OK

:db_done
set PGPASSWORD=

echo.
echo  ================================================================
echo    SETUP COMPLETE!
echo  ================================================================
echo.
echo  Double-click START_SERVER.bat to start the server.
echo  Then open any browser on the network and go to:
echo    http://THIS-SERVER-IP:3000
echo.
pause
