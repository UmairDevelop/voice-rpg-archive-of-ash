@echo off
title The Archive of Ash - Launcher
echo ========================================================
echo          THE ARCHIVE OF ASH - VOICE RPG ENCOUNTER
echo ========================================================
echo.

cd /d "%~dp0"

if exist "dist\TheArchiveOfAsh\TheArchiveOfAsh.exe" (
    echo Launching standalone Windows executable...
    start "" "dist\TheArchiveOfAsh\TheArchiveOfAsh.exe"
    exit /b 0
)

echo Launching Pygame Game Client via Python...
python -m src.client.main

if %errorlevel% neq 0 (
    echo.
    echo [NOTICE] Game exited with error code %errorlevel%.
    pause
)
