# 🔧 Gerador de Código PLC

Sistema automatizado para gerar código Ladder (Rockwell Studio 5000) e SCL (Siemens TIA Portal) a partir de dados de ativação armazenados em banco de dados SQL Server.

**Desenvolvido com princípios SOLID, KISS e DRY**

---

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.7 ou superior
- ODBC Driver 17 for SQL Server
- Acesso a banco de dados SQL Server

### Instalação

```bash
pip install -r requirements.txt
```

### Executar Aplicação

#### Opção 1: Interface Web (Recomendado)

**Windows:**
```bash
# Clique duas vezes em:
start_server.bat

# Ou execute:
python app.py
```

Acesse: **http://localhost:8080** (ou a porta exibida no terminal)

**Nota:** O sistema busca automaticamente uma porta disponível entre 8080-8089.

#### Opção 2: Interface CLI

**Windows:**
```bash
# Clique duas vezes em:
start_cli.bat

# Ou execute:
python PLC_CodeGenerator.py
```

---

## 💡 Funcionalidades

### Interface Web

✅ Conexão em duas etapas (servidor → banco de dados)
✅ Dashboard visual com status em tempo real
✅ Dropdown com lista de bancos disponíveis
✅ Geração de código com um clique
✅ Preview dos arquivos no navegador
✅ Download individual de arquivos
✅ Visualização de configurações
✅ Design responsivo moderno (Tabler.io)

### Códigos Gerados

1. **rockwell_ladder.txt** - Código Ladder em formato texto legível
2. **rockwell_ladder.L5X** - Arquivo XML para importação no Studio 5000
3. **siemens_scl.scl** - Código SCL para Siemens TIA Portal

---

## 📋 Como Usar (Interface Web)

### 1. Conectar ao Servidor SQL

**Etapa 1:**
1. Digite o **servidor** (ex: localhost ou IP)
2. (Opcional) Marque **"Usar autenticação SQL"** e preencha usuário/senha
3. Clique em **"Listar Bancos de Dados"**

**Etapa 2:**
1. Selecione o banco desejado no **dropdown**
2. Clique em **"Conectar"**

### 2. Gerar Códigos PLC

1. Após conectar, clique em **"Gerar Códigos PLC"**
2. Aguarde o processamento
3. Veja a seção **"Arquivos Gerados"**

### 3. Visualizar e Baixar

- **👁️ Visualizar**: Preview do código no navegador
- **⬇️ Baixar**: Download do arquivo

---

## 📊 Estrutura do Banco de Dados

O sistema espera as seguintes tabelas no SQL Server:

### tblPhaseSteps

- `iClassID` - Identificador da fase
- `iIndexNo` - Número do step
- `sName_1` - Nome do step

### tblPhaseActivation

- `iPhaseID` - Liga com tblPhaseSteps.iClassID
- `iStepNo` - Liga com tblPhaseSteps.iIndexNo
- `iPIDType` - Tipo de PID (0 se não for PID)
- `iType` - Identificador do tipo de componente
- `sName_1` - Nome da tag

---

## ⚙️ Configuração

O sistema usa `plc_config.json` (criado automaticamente) para mapear tipos e sufixos:

### Tipos de Componentes (iType)

- 0: Valve
- 6: Analog Output
- 8: PID
- 10: Communication
- 13: VSD

### Sufixos de Ativação

- Valve → `.Activate`
- Analog Output → `.Activate`
- VSD → `.Activate`
- Communication → (sem sufixo)
- PID → `.FixedOutput` (se pid_type == 4) ou `.ClosedLoop` (outros)

### Editar Mapeamentos

Edite `plc_config.json`:

```json
{
    "type_mapping": {
        "0": "Valve",
        "14": "Novo Tipo"
    },
    "suffix_mapping": {
        "Novo Tipo": ".NovoSufixo"
    }
}
```

Clique em **"Atualizar Configurações"** na interface web.

---

## 🔌 APIs REST

### Banco de Dados

```bash
# Listar bancos de dados disponíveis
POST /api/database/list-databases
Body: {"server": "localhost", "username": "sa", "password": "pass"}

# Conectar ao banco
POST /api/database/connect
Body: {"server": "localhost", "database": "MyDB"}

# Status da conexão
GET /api/database/status
```

### Geração

```bash
# Gerar códigos PLC
POST /api/generate
Body: {"output_dir": "output"}

# Preview de arquivo
GET /api/preview/<filename>?output_dir=output

# Download de arquivo
GET /api/download/<filename>?output_dir=output
```

### Configurações

```bash
# Obter configurações
GET /api/config

# Atualizar configurações
POST /api/config
Body: {"type_mapping": {...}, "suffix_mapping": {...}}
```

---

## 🏗️ Arquitetura

### Componentes Principais

- **ConfigManager** - Gerencia mapeamentos de tipos e sufixos
- **DatabaseConnection** - Conexão e consultas ao SQL Server
- **RockwellGenerator** - Geração de código Ladder (.txt e .L5X)
- **SiemensGenerator** - Geração de código SCL
- **PLCCodeGenerator** - Orquestrador principal
- **Flask App** - Interface web e APIs REST

### Princípios de Desenvolvimento

✅ **SOLID** - Design orientado a objetos
✅ **KISS** - Código simples e direto
✅ **DRY** - Reutilização máxima de código

Consulte **CLAUDE.md** para detalhes técnicos completos.

---

## 🔧 Comandos Úteis

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Verificar instalação
pip list | findstr "Flask pyodbc"
```

### Execução

```bash
# Interface Web
python app.py

# Interface CLI
python PLC_CodeGenerator.py

# Com Waitress (produção)
waitress-serve --host=0.0.0.0 --port=8080 app:app
```

### Testes

```bash
# Testar importações
python -c "from app import app; print('OK')"

# Testar conexão (exemplo)
python -c "from PLC_CodeGenerator import DatabaseConnection; db = DatabaseConnection('localhost', 'TestDB'); db.connect()"
```

### SQL Server

```sql
-- Verificar tabelas
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME IN ('tblPhaseSteps', 'tblPhaseActivation');

-- Contar ativações
SELECT COUNT(*) as Total
FROM dbo.tblPhaseActivation
WHERE sName_1 IS NOT NULL;

-- Visualizar dados
SELECT TOP 10 t2.iIndexNo, t2.sName_1 as StepName, t1.sName_1 as TagName
FROM dbo.tblPhaseSteps t2
LEFT JOIN dbo.tblPhaseActivation t1
    ON t2.iClassID = t1.iPhaseID AND t2.iIndexNo = t1.iStepNo
WHERE t1.sName_1 IS NOT NULL;
```

---

## ⚠️ Troubleshooting

### Erro de Conexão ao Banco

**Soluções:**
- Verifique se SQL Server está rodando
- Confirme nome do servidor e banco
- Teste com SQL Server Management Studio
- Verifique firewall e permissões

### Erro "Import flask could not be resolved"

```bash
pip install Flask flask-cors
```

### Erro "pyodbc not found"

```bash
pip install pyodbc
```

Se persistir, instale [ODBC Driver 17 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### Porta em Uso

**Resolvido!** O sistema busca automaticamente uma porta disponível (8080-8089).

Se ainda tiver problemas:
```bash
# Ver portas em uso
netstat -ano | findstr :8080

# Finalizar processo
taskkill /PID [PID_NUMBER] /F
```

### Nenhuma Ativação Encontrada

**Causas:**
- Banco de dados vazio
- Tabelas não existem
- Campo `sName_1` está NULL

**Solução:**
```sql
SELECT COUNT(*) FROM dbo.tblPhaseActivation WHERE sName_1 IS NOT NULL
```

---

## 📂 Estrutura de Arquivos

```
PLC CodeGenerator/
├── PLC_CodeGenerator.py    # Código principal (CLI)
├── app.py                   # Servidor Flask (Web)
├── requirements.txt         # Dependências
├── plc_config.json         # Configurações (auto-criado)
├── templates/
│   └── index.html          # Interface web
├── output/                 # Arquivos gerados (auto-criado)
│   ├── rockwell_ladder.txt
│   ├── rockwell_ladder.L5X
│   └── siemens_scl.scl
├── README.md               # Este arquivo
├── CLAUDE.md               # Documentação técnica
├── start_server.bat        # Iniciar interface web
└── start_cli.bat           # Iniciar interface CLI
```

---

## 🎨 Tecnologias

- **Backend:** Python 3.7+, Flask 3.0.0
- **Frontend:** HTML5, CSS3, JavaScript, Tabler.io
- **Database:** SQL Server (pyodbc 5.0.1)
- **Design:** Tabler.io framework
- **Cores:** #000F41 (Principal), #1F9DFF (Secundária), #F0F0F0 (Contraste)

---

## 📝 Exemplo Completo

```bash
# 1. Iniciar servidor
start_server.bat

# 2. Acessar
http://localhost:8080

# 3. Etapa 1: Conectar ao servidor
#    Servidor: localhost
#    Autenticação: Windows

# 4. Etapa 2: Selecionar banco
#    Banco: PLCDatabase

# 5. Gerar códigos
#    Clique em "Gerar Códigos PLC"

# 6. Visualizar/Baixar
#    Use os botões 👁️ Ver ou ⬇️ Baixar

# 7. Importar
#    Studio 5000: rockwell_ladder.L5X
#    TIA Portal: siemens_scl.scl
```

---

## 🔐 Produção

### Usar Waitress

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=8080 app:app
```

### HTTPS

Use um reverse proxy (nginx/Apache) ou configure certificados SSL.

---

## 📖 Documentação Adicional

- **CLAUDE.md** - Arquitetura detalhada, padrões de código, troubleshooting
- **PLC_CodeGenerator.py** - Código fonte comentado
- **app.py** - APIs REST e rotas

---

## 🆘 Suporte

Para questões técnicas:
1. Consulte este README
2. Veja CLAUDE.md para detalhes de arquitetura
3. Examine o código fonte comentado

---

## 📊 Recursos

### Dependências

```
Flask==3.0.0
flask-cors==4.0.0
pyodbc==5.0.1
waitress==2.1.2
```

### Requisitos do Sistema

- Python 3.7+
- ODBC Driver 17 for SQL Server
- Windows (testado), Linux/Mac (compatível)

---

## ✅ Status do Projeto

**Status:** ✅ Completo e Funcional
**Última Atualização:** 12/11/2025
**Versão:** 2.0 (com conexão em duas etapas)

### Funcionalidades Implementadas

✅ Interface web moderna com Tabler.io
✅ Conexão em duas etapas com dropdown de bancos
✅ Detecção automática de porta disponível
✅ Geração de código Ladder e SCL
✅ Preview e download de arquivos
✅ Configurações editáveis
✅ APIs REST completas
✅ Design responsivo

---

**Desenvolvido com ❤️ seguindo os princípios SOLID, KISS e DRY**
