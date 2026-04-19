@echo off
rem Wraps cargo with MSVC env (vcvars64.bat) so builds work from non-Developer shells.
rem Uses the standalone Build Tools for VS 2022 (proper desktop C++ workload).
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
pushd "%~dp0\..\src-tauri"
cargo %*
set CARGO_EXIT=%ERRORLEVEL%
popd
exit /b %CARGO_EXIT%
