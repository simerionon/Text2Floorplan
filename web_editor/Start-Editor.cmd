@echo off
setlocal
cd /d "%~dp0.."
if defined TEXT2REVIT_PYTHON (
    "%TEXT2REVIT_PYTHON%" -m web_editor.server --open %*
    goto finish
)
if exist "%USERPROFILE%\miniconda3\envs\Text2Revit\python.exe" (
    "%USERPROFILE%\miniconda3\envs\Text2Revit\python.exe" -m web_editor.server --open %*
    goto finish
)
for /f "delims=" %%D in ('dir /b /ad /o-d "%LOCALAPPDATA%\Text2Revit\releases" 2^>nul') do (
    if exist "%LOCALAPPDATA%\Text2Revit\releases\%%D\installed.txt" (
        if exist "%LOCALAPPDATA%\Text2Revit\releases\%%D\runtime\python.exe" (
            set "TEXT2REVIT_RUNTIME=%LOCALAPPDATA%\Text2Revit\releases\%%D\runtime"
            goto bundled
        )
    )
)
python -m web_editor.server --open %*
goto finish
:bundled
set "PATH=%TEXT2REVIT_RUNTIME%;%TEXT2REVIT_RUNTIME%\Library\bin;%TEXT2REVIT_RUNTIME%\DLLs;%PATH%"
"%TEXT2REVIT_RUNTIME%\python.exe" -m web_editor.server --open %*
:finish
if errorlevel 1 (
    echo.
    echo The editor could not start. See web_editor\README.md for setup instructions.
    pause
)
