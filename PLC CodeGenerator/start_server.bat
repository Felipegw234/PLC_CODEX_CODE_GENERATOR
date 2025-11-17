@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cls
echo ========================================
echo   GERADOR DE CODIGO PLC - Interface Web
echo   Rockwell Studio 5000 ^| Siemens TIA Portal
echo ========================================
echo.
echo Iniciando servidor...
echo.

REM Inicia o servidor em background
start /B python app.py

REM Aguarda o servidor iniciar
timeout /t 3 /nobreak > nul

REM Abre o navegador automaticamente
start http://localhost:8080

echo.
echo ========================================
echo   Servidor em execucao!
echo   O navegador foi aberto automaticamente
echo ========================================
echo.
echo Pressione qualquer tecla para finalizar o servidor...
pause > nul
taskkill /F /IM python.exe 2>nul
