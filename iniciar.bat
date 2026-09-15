@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    py -3 main.py
)
if errorlevel 1 (
    echo.
    echo Consulte README.md para instalar Python e as dependencias.
    pause
)
endlocal
