@echo off
echo.
echo ======================================================
echo           Iniciando la aplicacion Taller Mecanico
echo ======================================================
echo.

REM Cambiar al directorio del script
cd /d %~dp0
echo Paso 1: Directorio actual: %cd%
pause

@echo off
echo Iniciando la aplicacion de Taller Mecanico...

REM Cambiar al directorio del script
cd /d %~dp0

REM Activar el entorno virtual
call venv\Scripts\activate.bat

REM Iniciar la aplicacion Flask en segundo plano
start /b python app.py

REM Esperar un momento para que el servidor inicie
timeout /t 5 >nul

REM Abrir el navegador en la URL de la aplicacion
start "" "http://127.0.0.1:5000"

echo.
echo El servidor esta funcionando. No cierres esta ventana.
echo Para detener la aplicacion, presiona Ctrl+C en esta ventana.
pause