@echo off
rem Wraps `pnpm tauri dev` with MSVC env so Rust can link from any shell.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
pushd "%~dp0\.."
pnpm tauri dev
set EXIT=%ERRORLEVEL%
popd
exit /b %EXIT%
