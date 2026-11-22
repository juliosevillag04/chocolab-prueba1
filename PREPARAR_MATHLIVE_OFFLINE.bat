@echo off
setlocal
cd /d "%~dp0"
title Preparar editor MathLive sin Internet
where npm.cmd >nul 2>nul
if errorlevel 1 (
 echo No se encontro npm. Instala Node.js y vuelve a intentarlo.
 pause
 exit /b 1
)
if not exist "node_modules\mathlive\mathlive.min.js" (
 echo Descargando MathLive mediante npm...
 call npm.cmd install --no-save mathlive
 if errorlevel 1 (
   echo No se pudo instalar MathLive. Revisa tu conexion a Internet.
   pause
   exit /b 1
 )
)
if not exist "static\vendor" mkdir "static\vendor"
copy /Y "node_modules\mathlive\mathlive.min.js" "static\vendor\mathlive.min.js" >nul
if not exist "static\vendor\fonts" mkdir "static\vendor\fonts"
xcopy /E /I /Y "node_modules\mathlive\fonts" "static\vendor\fonts" >nul
if exist "node_modules\mathlive\sounds" (
 if not exist "static\vendor\sounds" mkdir "static\vendor\sounds"
 xcopy /E /I /Y "node_modules\mathlive\sounds" "static\vendor\sounds" >nul
)
echo.
echo MathLive ya esta guardado localmente.
echo Ahora inicia la aplicacion con INICIAR_CHOCOLAB.bat
pause
endlocal
