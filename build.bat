@echo off
title Twickenham Health — Build EXE
color 1F

echo.
echo ============================================================
echo   Twickenham Health Limited — Invoice App Builder
echo ============================================================
echo.

:: ── Check Python is available ────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    echo         and make sure it is added to PATH.
    pause
    exit /b 1
)

:: ── Check PyInstaller is installed ───────────────────────────
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller not found. Installing now...
    pip install pyinstaller
)

:: ── Clean previous build ─────────────────────────────────────
echo [1/4] Cleaning previous build...
if exist dist\TwickenhamHealth.exe (
    del /f /q dist\TwickenhamHealth.exe
    echo       Previous .exe removed.
) else (
    echo       Nothing to clean.
)

if exist build (
    rmdir /s /q build
)

if exist TwickenhamHealth.spec (
    del /f /q TwickenhamHealth.spec
)

:: ── Check for logo ───────────────────────────────────────────
echo.
echo [2/4] Checking assets...
set LOGO_FOUND=
if exist assets\logo.png set LOGO_FOUND=1
if exist assets\twickenham_health_logo.png set LOGO_FOUND=1
if defined LOGO_FOUND (
    echo       Logo found — will be included.
    if exist assets\logo.ico (
        set ICON_FLAG=--icon=assets\logo.ico
    ) else (
        set ICON_FLAG=
    )
) else (
    echo       No logo found in assets\ — building without icon.
    set ICON_FLAG=
)

:: ── Run PyInstaller ──────────────────────────────────────────
echo.
echo [3/4] Building EXE with PyInstaller...
echo       This may take 1-3 minutes, please wait...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "TwickenhamHealth" ^
    --add-data "assets;assets" ^
    --add-data "database;database" ^
    %ICON_FLAG% ^
    main.py

:: ── Check result ─────────────────────────────────────────────
echo.
echo [4/4] Checking output...
if exist dist\TwickenhamHealth.exe (
    echo.
    echo ============================================================
    echo   SUCCESS! Your app is ready:
    echo.
    echo   dist\TwickenhamHealth.exe
    echo.
    echo   Copy this .exe file to any Windows 11 PC and run it.
    echo   No Python installation needed on the target PC.
    echo ============================================================
    echo.
    :: Open the dist folder in Windows Explorer
    explorer dist
) else (
    echo.
    echo ============================================================
    echo   [ERROR] Build failed. Check the output above for errors.
    echo ============================================================
)

echo.
pause