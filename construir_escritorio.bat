@echo off
setlocal
cd /d "%~dp0"
python -c "import tkinter; from topored.analisis import analizar; from topored.reporte import generar_reporte" 
if errorlevel 1 goto error
python -m PyInstaller --noconfirm --onedir --name TopoRedEscritorio --workpath "%LOCALAPPDATA%\TopoRedEscritorio_build" --distpath "%LOCALAPPDATA%\TopoRedEscritorio_dist" --exclude-module pandas --exclude-module streamlit --exclude-module matplotlib app_escritorio.py
if errorlevel 1 goto error
xcopy /E /I /Y ejemplos "%LOCALAPPDATA%\TopoRedEscritorio_dist\TopoRedEscritorio\ejemplos"
if errorlevel 1 goto error
echo Paquete generado. Falta probar el arranque y analisis.
explorer "%LOCALAPPDATA%\TopoRedEscritorio_dist"
exit /b 0
:error
echo El proceso fallo. Revisa el mensaje anterior.
exit /b 1
