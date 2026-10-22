@echo off
chcp 65001 >nul
title Cannondale Bike Intelligence - Analise de Dados

echo.
echo ========================================================================
echo   CANNONDALE BIKE INTELLIGENCE - ANALISE DE DADOS (TERMINAL)
echo ========================================================================
echo.

:: Detecta o diretorio onde este .bat esta localizado
set "RAIZ=%~dp0"
cd /d "%RAIZ%"

if not exist "dashboard\analise_terminal.py" (
    echo ERRO: arquivo dashboard\analise_terminal.py nao encontrado em "%RAIZ%".
    echo Certifique-se de que esta na raiz do projeto CANNONDALE DATA & BI PLATFORM.
    echo.
    pause
    exit /b 1
)

echo Iniciando consulta ao PostgreSQL (Docker: cannondale-pg, porta 5433)...
echo.

python dashboard\analise_terminal.py

if %errorlevel% neq 0 (
    echo.
    echo ERRO ao executar a analise. Verifique se o container esta ativo:
    echo   docker start cannondale-pg
)

echo.
pause
