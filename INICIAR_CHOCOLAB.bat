@echo off
setlocal
cd /d "%~dp0"
title Choco Lab - Laboratorio matematico
where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    set "PY=python"
)
%PY% -c "import flask, numpy, sympy, plotly" >nul 2>nul
if errorlevel 1 (
    echo.
    echo Faltan dependencias. Se intentaran instalar con pip...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo No se pudieron instalar las dependencias.
        echo Ejecuta en una terminal: python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo.
echo Choco Lab iniciandose en http://127.0.0.1:5000
%PY% app.py
if errorlevel 1 pause
endlocal
