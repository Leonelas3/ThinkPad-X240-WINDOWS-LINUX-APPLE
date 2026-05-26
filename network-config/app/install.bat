@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ============================================================
echo    Instalador - Gestión Red Doméstica
echo ============================================================
echo.

:: Comprobar Python 3.10+
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo.
    echo Opciones para instalar Python:
    echo  1. Microsoft Store: busca "Python 3.12" y pulsa Instalar
    echo  2. Web oficial: https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Durante la instalación marca "Add Python to PATH"
    echo.
    start ms-windows-store://pdp/?ProductId=9NCVDN91XZQP
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set PYMAJ=%%a
    set PYMIN=%%b
)

if !PYMAJ! LSS 3 (
    echo [ERROR] Se necesita Python 3.10 o superior. Versión detectada: !PYVER!
    goto instalar_python
)
if !PYMAJ! EQU 3 if !PYMIN! LSS 10 (
    echo [ERROR] Se necesita Python 3.10 o superior. Versión detectada: !PYVER!
    goto instalar_python
)

echo [OK] Python !PYVER! detectado.
echo.

:: Crear entorno virtual
set APP_DIR=%~dp0
set VENV_DIR=%APP_DIR%venv

echo Creando entorno virtual en %VENV_DIR% ...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)
echo [OK] Entorno virtual creado.
echo.

:: Instalar dependencias
echo Instalando dependencias desde requirements.txt ...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%VENV_DIR%\Scripts\pip.exe" install -r "%APP_DIR%requirements.txt"
if errorlevel 1 (
    echo [ERROR] Falló la instalación de dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.
echo.

:: Crear acceso directo en el escritorio
echo Creando acceso directo en el escritorio ...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\Red Doméstica.lnk
set PYTHONW="%VENV_DIR%\Scripts\pythonw.exe"
set MAIN_SCRIPT="%APP_DIR%main.py"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%SHORTCUT%'); ^
   $sc.TargetPath = '%VENV_DIR%\Scripts\pythonw.exe'; ^
   $sc.Arguments = '\"%APP_DIR%main.py\"'; ^
   $sc.WorkingDirectory = '%APP_DIR%'; ^
   $sc.Description = 'Gestión Red Doméstica 192.168.50.0/24'; ^
   $sc.Save()"

if errorlevel 1 (
    echo [AVISO] No se pudo crear el acceso directo automáticamente.
    echo Puedes ejecutar la app manualmente con:
    echo   %VENV_DIR%\Scripts\pythonw.exe %APP_DIR%main.py
) else (
    echo [OK] Acceso directo creado en el escritorio.
)

echo.
echo ============================================================
echo  Instalación completa. Usa el acceso directo 'Red Doméstica' en el escritorio.
echo ============================================================
echo.
pause
exit /b 0

:instalar_python
echo.
echo Abriendo Microsoft Store para instalar Python...
start ms-windows-store://pdp/?ProductId=9NCVDN91XZQP
echo.
echo Si la Store no abre, visita: https://www.python.org/downloads/
echo Instala Python 3.10 o superior y vuelve a ejecutar este script.
echo.
pause
exit /b 1
