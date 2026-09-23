@echo off
setlocal
cd /d "%~dp0"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY (
    where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
    echo Error: Python 3 not found. Install it from https://www.python.org/ and tick "Add Python to PATH" during setup.
    pause
    exit /b 1
)

where gcc >nul 2>nul
if errorlevel 1 (
    echo Error: gcc not found. Install MinGW-w64 and add its bin folder to PATH.
    pause
    exit /b 1
)

echo Building analyzer.exe ...
gcc -Wall -Wextra -std=c99 -o analyzer.exe analyzer.c
if errorlevel 1 (
    echo Error: compilation of analyzer.c failed.
    pause
    exit /b 1
)

if not exist data mkdir data

%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo Error: tkinter is missing. Reinstall Python and keep the Tcl/Tk option enabled.
    pause
    exit /b 1
)

%PY% -m py_compile app.py
if errorlevel 1 (
    echo Error: app.py failed syntax check.
    pause
    exit /b 1
)

echo Starting shieldHer ...
%PY% app.py
pause