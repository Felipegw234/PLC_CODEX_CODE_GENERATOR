PASTA STATIC - Recursos Estaticos
===================================

Esta pasta contem recursos estaticos (CSS, JavaScript, imagens) utilizados pela interface web.

ESTRUTURA:

static/
├── image/
│   └── GEA_Logo_w_Claim_sRGB_Solid_neg.svg  (Logo GEA - OBRIGATORIO)
├── css/      (opcional - CSS customizados)
└── js/       (opcional - JavaScript customizados)

IMPORTANTE:
-----------
1. O arquivo GEA_Logo_w_Claim_sRGB_Solid_neg.svg e OBRIGATORIO
   - Coloque o logo da GEA nesta pasta antes de fazer o build

2. Os arquivos desta pasta serao automaticamente incluidos no executavel
   pelo PyInstaller

3. A maioria dos CSS/JS vem de CDN (nao precisa incluir aqui):
   - Tabler CSS: https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta19/
   - Tabler Icons: https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/

OBSERVACAO:
-----------
Se voce adicionar CSS ou JS customizados, coloque nas respectivas pastas
e atualize as referencias no arquivo templates/index.html
