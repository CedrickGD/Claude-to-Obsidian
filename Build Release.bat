@echo off
rem ============================================================
rem  Claude to Obsidian — Release Builder
rem  Double-click to produce the shippable .exe + MSI + NSIS
rem  installer. ~2-3 min on subsequent runs (deps cached).
rem
rem  Output lands in:
rem    src-tauri\target\release\claude-to-obsidian.exe
rem    src-tauri\target\release\bundle\msi\*.msi
rem    src-tauri\target\release\bundle\nsis\*.exe
rem ============================================================

title Claude to Obsidian - Build Release
cd /d "%~dp0"

echo.
echo   Building release artifacts (exe + MSI + NSIS installer)...
echo.

call "scripts\tauri-build.bat"
set BUILD_EXIT=%ERRORLEVEL%

if %BUILD_EXIT% EQU 0 (
  echo.
  echo   =====================================================
  echo   Build succeeded. Artifacts at:
  echo     src-tauri\target\release\claude-to-obsidian.exe
  echo     src-tauri\target\release\bundle\msi\
  echo     src-tauri\target\release\bundle\nsis\
  echo   =====================================================
  echo.
  echo   Opening the release folder...
  start "" "src-tauri\target\release"
) else (
  echo.
  echo   Build failed with exit code %BUILD_EXIT%.
)

echo.
echo   Press any key to close.
pause >nul
exit /b %BUILD_EXIT%
