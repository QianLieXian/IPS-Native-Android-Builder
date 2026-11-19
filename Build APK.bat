@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Apk.ps1" %*
set "IPS_EXIT=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %IPS_EXIT%
