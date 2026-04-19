@echo off
rem Wraps `pnpm tauri build` with MSVC env so the release bundle links correctly.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
pushd "%~dp0\.."
pnpm tauri build
set EXIT=%ERRORLEVEL%
popd
exit /b %EXIT%
