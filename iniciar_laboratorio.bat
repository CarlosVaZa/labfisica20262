@echo off
setlocal
title Laboratorio de Fisica - Grupo 1
cd /d "%~dp0"
if errorlevel 1 goto carpeta_error

echo ======================================================================
echo    GRUPO 1 - LABORATORIO DE FISICA: VELOCIDAD DEL SONIDO POR RESONANCIA
echo ======================================================================
echo Iniciando Interfaz Visual...

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0main.py"
    if errorlevel 1 goto inicio_error
    exit /b 0
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0main.py"
    if errorlevel 1 goto inicio_error
    exit /b 0
)

where python >nul 2>&1
if not errorlevel 1 (
    python "%~dp0main.py"
    if errorlevel 1 goto inicio_error
    exit /b 0
)

echo No se encontro Python. Instala Python 3 con Tcl/Tk para abrir la interfaz.
pause
exit /b 1

:inicio_error
echo.
echo No se pudo iniciar la interfaz. Revisa el error que aparece arriba.
echo Para instalar las dependencias, abre una terminal en esta carpeta y ejecuta:
if exist "%~dp0.venv\Scripts\python.exe" (
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo   py -3 -m pip install -r requirements.txt
)
pause
exit /b 1

:carpeta_error
echo No se pudo abrir la carpeta del laboratorio.
pause
exit /b 1
