@echo off
REM ============================================================================
REM Script para configurar la tarea programada del Auditor Neotel
REM Se ejecutará automáticamente cada noche a las 23:00
REM ============================================================================

echo.
echo ========================================================================
echo   CONFIGURADOR DE TAREA PROGRAMADA - AUDITOR NEOTEL
echo ========================================================================
echo.

REM Obtener la ruta actual del script
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%neotel_config_extractor.py
set PYTHON_EXE=python

echo [INFO] Directorio del script: %SCRIPT_DIR%
echo [INFO] Ruta del script Python: %SCRIPT_PATH%
echo.

REM Verificar que existe el script Python
if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encuentra el archivo neotel_config_extractor.py
    echo [ERROR] Asegurate de que este archivo .bat esta en la misma carpeta
    pause
    exit /b 1
)

echo [OK] Script Python encontrado
echo.

REM Verificar que Python esta instalado
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo [INFO] Instala Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Verificar/instalar dependencias
echo [INFO] Verificando dependencias de Python...
%PYTHON_EXE% -m pip install --upgrade pip >nul 2>&1
%PYTHON_EXE% -m pip install selenium pyodbc pandas psutil chardet >nul 2>&1

if errorlevel 1 (
    echo [WARNING] Hubo problemas instalando algunas dependencias
    echo [INFO] Ejecuta manualmente: pip install selenium pyodbc pandas psutil chardet
) else (
    echo [OK] Dependencias instaladas/verificadas
)
echo.

REM Crear tarea programada
echo [INFO] Creando tarea programada en Windows Task Scheduler...
echo.

REM Eliminar tarea si ya existe
schtasks /query /tn "NeotelConfigAuditor" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Eliminando tarea existente...
    schtasks /delete /tn "NeotelConfigAuditor" /f >nul 2>&1
)

REM Crear nueva tarea programada
REM - Se ejecuta diariamente a las 23:00
REM - Usuario: SYSTEM (se ejecuta aunque no haya sesión iniciada)
REM - Máxima prioridad
REM - Se ejecuta incluso si está con batería

schtasks /create ^
    /tn "NeotelConfigAuditor" ^
    /tr "\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\"" ^
    /sc daily ^
    /st 23:00 ^
    /ru SYSTEM ^
    /rl HIGHEST ^
    /f

if errorlevel 1 (
    echo [ERROR] No se pudo crear la tarea programada
    echo [INFO] Verifica que tienes permisos de administrador
    echo [INFO] Ejecuta este .bat como Administrador (click derecho -^> Ejecutar como administrador)
    pause
    exit /b 1
)

echo.
echo [OK] Tarea programada creada exitosamente
echo.

REM Mostrar información de la tarea
echo ========================================================================
echo   CONFIGURACION DE LA TAREA
echo ========================================================================
echo.
echo Nombre:            NeotelConfigAuditor
echo Horario:           Todos los dias a las 23:00
echo Usuario:           SYSTEM
echo Script:            %SCRIPT_PATH%
echo Estado:            Activada
echo.

REM Preguntar si quiere ejecutar ahora para probar
echo ========================================================================
echo.
set /p EJECUTAR="Deseas ejecutar una prueba AHORA? (S/N): "

if /i "%EJECUTAR%"=="S" (
    echo.
    echo [INFO] Ejecutando auditor (esto puede tardar varios minutos)...
    echo.
    "%PYTHON_EXE%" "%SCRIPT_PATH%"
    
    if errorlevel 1 (
        echo.
        echo [ERROR] La ejecucion de prueba fallo
        echo [INFO] Revisa los logs en: %SCRIPT_DIR%NeotelConfigAudit\logs\
    ) else (
        echo.
        echo [OK] Ejecucion de prueba completada
        echo [INFO] Revisa tu email para verificar que funciona correctamente
    )
)

echo.
echo ========================================================================
echo   PROXIMOS PASOS
echo ========================================================================
echo.
echo 1. La tarea se ejecutara automaticamente cada noche a las 23:00
echo 2. Los reportes se guardaran en: %SCRIPT_DIR%NeotelConfigAudit\
echo 3. Los logs estan en: %SCRIPT_DIR%NeotelConfigAudit\logs\
echo 4. Recibiras un email diario con los cambios detectados
echo.
echo Para DESACTIVAR la tarea:
echo    - Abre "Programador de tareas" de Windows
echo    - Busca "NeotelConfigAuditor"
echo    - Click derecho -^> Deshabilitar
echo.
echo Para ELIMINAR la tarea:
echo    schtasks /delete /tn "NeotelConfigAuditor" /f
echo.
echo ========================================================================
echo.

pause