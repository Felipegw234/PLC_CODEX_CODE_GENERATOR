@echo off
chcp 65001
set PYTHONIOENCODING=utf-8
cls
echo ========================================
echo   GERADOR DE CODIGO PLC - Interface CLI
echo   Rockwell Studio 5000 ^| Siemens TIA Portal
echo ========================================
echo.
python PLC_CodeGenerator.py
echo.
pause
