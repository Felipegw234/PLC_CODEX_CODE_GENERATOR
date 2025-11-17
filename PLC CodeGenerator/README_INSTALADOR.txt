================================================================================
  GERADOR DE CODIGO PLC - GUIA RAPIDO DE BUILD
================================================================================

PROBLEMA RESOLVIDO:
-------------------
O executavel agora inclui TODOS os recursos estaticos (CSS, logo, etc.)
A interface web nao ficara mais "bugada"!


COMO FAZER O BUILD:
-------------------

1. EXECUTAVEL SIMPLES (para testes):

   > build_executable.bat

   Resultado: dist\PLCCodeGenerator.exe


2. EXECUTAVEL + INSTALADOR (para distribuir ao time):

   > build_installer.bat

   Resultado:
   - dist\PLCCodeGenerator.exe
   - installer_output\PLCCodeGenerator_Setup_v1.0.0.exe


O QUE FOI CORRIGIDO:
--------------------

1. Pasta static/ foi criada e sera incluida no build
2. Logo GEA placeholder foi criado em: static/image/GEA_Logo_w_Claim_sRGB_Solid_neg.svg
3. Arquivo .spec atualizado para incluir recursos estaticos
4. Instalador criado com Inno Setup (detecta ODBC Driver automaticamente)


IMPORTANTE:
-----------

- Para usar o logo GEA real, substitua:
  static/image/GEA_Logo_w_Claim_sRGB_Solid_neg.svg

- Para gerar instalador, precisa instalar Inno Setup:
  https://jrsoftware.org/isdl.php

- Se nao quiser instalador, use apenas: build_executable.bat


DISTRIBUIR:
-----------

Opcao A: Distribua apenas: dist\PLCCodeGenerator.exe
Opcao B: Distribua o instalador: installer_output\PLCCodeGenerator_Setup_v1.0.0.exe (RECOMENDADO)


DOCUMENTACAO COMPLETA:
----------------------

Leia BUILD.md para informacoes detalhadas sobre:
- Pre-requisitos
- Recursos estaticos
- Troubleshooting
- Versionamento


================================================================================
