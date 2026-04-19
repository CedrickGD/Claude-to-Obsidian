@echo off
rem ============================================================
rem  Claude to Obsidian — Dev Launcher
rem  Double-click to start the app in dev mode (HMR enabled).
rem  First run compiles ~500 Rust crates (5-10 min); later runs
rem  are seconds. Leave this window open while using the app;
rem  closing it shuts the app down.
rem ============================================================

title Claude to Obsidian - Dev
cd /d "%~dp0"

echo.
echo   Launching Claude to Obsidian...
echo.

call "scripts\tauri-dev.bat"

if errorlevel 1 (
  echo.
  echo   Launch failed. Press any key to close.
  pause >nul
)
