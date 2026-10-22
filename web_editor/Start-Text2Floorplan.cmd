@echo off
setlocal
cd /d "%~dp0"
if not exist "web_editor\server.py" cd /d "%~dp0.."
if not exist "web_editor\server.py" (
    echo The package is incomplete. Extract the complete ZIP before starting.
    pause
    exit /b 1
)
if exist "web_editor\release.json" (
    set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules;%ProgramFiles%\WindowsPowerShell\Modules"
    "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "web_editor\Prepare-Portable.ps1"
    if errorlevel 1 (
        echo Preparation failed. Keep the data ZIPs beside this folder and try again.
        pause
        exit /b 1
    )
)
if not exist "runtime\python.exe" (
    echo This launcher requires the complete Windows release. For source use web_editor\Start-Editor.cmd.
    pause
    exit /b 1
)
set "PATH=%CD%\runtime;%CD%\runtime\Library\bin;%CD%\runtime\DLLs;%PATH%"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONNOUSERSITE=1"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONIOENCODING=utf-8"
set "HF_HUB_OFFLINE=1"
set "HF_HUB_DISABLE_TELEMETRY=1"
set "TEXT2REVIT_CHECKPOINT=%CD%\models\flow_matching_best.pth"
set "TEXT2REVIT_CLIP_DIR=%CD%\models\clip"
echo Text2Floorplan - keep this window open while using the editor.
echo Close this window or press Ctrl+C to stop. Save your JSON before closing the browser.
"%CD%\runtime\python.exe" -B -m web_editor.server --port 0 --open %*
if errorlevel 1 pause
