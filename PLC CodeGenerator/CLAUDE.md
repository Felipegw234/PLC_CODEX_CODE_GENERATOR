# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANTE: Todas as respostas devem ser fornecidas em português brasileiro (pt-BR).**

## Padrões de Desenvolvimento

Este projeto segue os seguintes princípios de desenvolvimento:

- **SOLID** - Princípios de design orientado a objetos:
  - Single Responsibility: Cada classe tem uma única responsabilidade bem definida
  - Open/Closed: Classes abertas para extensão, fechadas para modificação
  - Liskov Substitution: Subtipos devem ser substituíveis por seus tipos base
  - Interface Segregation: Interfaces específicas são melhores que interfaces genéricas
  - Dependency Inversion: Dependa de abstrações, não de implementações concretas

- **KISS (Keep It Simple, Stupid)** - Mantenha o código simples e direto, evite complexidade desnecessária

- **DRY (Don't Repeat Yourself)** - Não repita código, reutilize e abstraia funcionalidades comuns

Ao fazer modificações ou adicionar novas funcionalidades, sempre siga estes princípios.

## Project Overview

This is a Python-based PLC code generator that reads phase activation data from a SQL Server database and generates ladder logic code for Rockwell Studio 5000 (.L5X format and text) and SCL code for Siemens TIA Portal.

**Core Purpose**: Automate the generation of PLC activation sequences based on phase steps stored in a SQL Server database, eliminating manual coding for repetitive activation logic.

## Running the Application

### Interface de Linha de Comando (CLI)

```bash
# Executar aplicação com menu interativo
python PLC_CodeGenerator.py
```

A aplicação CLI fornece um menu interativo para:
1. Conectar ao banco de dados SQL Server
2. Gerar arquivos de código
3. Editar mapeamentos de configuração
4. Sair

### Interface Web (Recomendado)

```bash
# Instalar dependências (primeira vez)
pip install -r requirements.txt

# Executar servidor web
python app.py

# Ou no Windows, clique duas vezes em:
start_server.bat
```

A interface web estará disponível em: **http://localhost:8080** (ou outra porta disponível)

**Nota:** O sistema busca automaticamente uma porta livre entre 8080-8089 usando a função `find_available_port()` em `app.py:231-240`. O endereço correto será exibido ao iniciar o servidor.

**Scripts de inicialização disponíveis:**
- `start_server.bat` - Inicia a interface web
- `start_cli.bat` - Inicia a interface CLI

**Recursos da Interface Web:**
- Dashboard visual com status de conexão em tempo real
- Formulário intuitivo para conexão com SQL Server
- Geração de código com um clique
- Preview dos arquivos gerados diretamente no navegador
- Download individual de arquivos
- Visualização das configurações de mapeamento
- Design responsivo e moderno

**APIs REST Disponíveis:**
- `GET /api/config` - Obter configurações atuais
- `POST /api/config` - Atualizar configurações
- `POST /api/database/connect` - Conectar ao banco de dados
- `GET /api/database/status` - Verificar status da conexão
- `POST /api/generate` - Gerar códigos PLC
- `GET /api/download/<filename>` - Download de arquivo
- `GET /api/preview/<filename>` - Preview de arquivo

## Dependencies

**Pacotes Python Necessários:**
- `pyodbc==5.0.1` - Conectividade com SQL Server (requer ODBC Driver 17 for SQL Server)
- `Flask==3.0.0` - Framework web para interface gráfica
- `flask-cors==4.0.0` - Suporte a CORS para APIs REST
- `waitress==2.1.2` - Servidor de produção (opcional)
- Biblioteca padrão: `json`, `os`, `typing`, `dataclasses`, `datetime`, `traceback`

**Instalação:**
```bash
pip install -r requirements.txt
```

**Requisitos do Sistema:**
- Python 3.7 ou superior
- ODBC Driver 17 for SQL Server
- Acesso a banco de dados SQL Server

## Architecture

### Main Components

1. **ConfigManager** (lines 18-80)
   - Manages type and suffix mappings via `plc_config.json`
   - Maps database `iType` values to PLC component types (Valve, PID, VSD, etc.)
   - Maps component types to activation suffixes (`.Activate`, `.ClosedLoop`, etc.)
   - Special handling for PID types: `pid_type_4` uses `.FixedOutput`, others use `.ClosedLoop`

2. **DatabaseConnection** (lines 82-162)
   - Connects to SQL Server using Windows authentication or SQL authentication
   - Queries two tables: `dbo.tblPhaseSteps` and `dbo.tblPhaseActivation`
   - Returns list of `Activation` dataclass objects
   - Key query joins phases with their activations, ordered by step number

3. **RockwellGenerator** (lines 164-251)
   - Generates Rockwell Ladder Logic in two formats:
     - Plain text format (`.txt`) - human-readable ladder rungs
     - L5X XML format (`.L5X`) - importable into Studio 5000
   - Each rung: `XIC(StepFlag[n].Flag)OTL(TagName.Suffix)`
   - Groups activations by step number

4. **SiemensGenerator** (lines 253-291)
   - Generates Siemens SCL code
   - Structure: IF-THEN blocks per step with multiple assignments
   - Format: `IF #MyStepFlag.Step{n} THEN ... := TRUE`
   - Uses REGION blocks for organization

5. **PLCCodeGenerator** (lines 293-401)
   - Main orchestrator class
   - Coordinates database connection, code generation, and config editing
   - `generate_all()` creates three output files in specified directory

6. **Flask Web Application** (app.py)
   - Servidor web Flask que expõe APIs REST
   - Interface HTML/CSS/JavaScript moderna e responsiva (templates/index.html)
   - Segue princípios SOLID: separação entre rotas, lógica de negócio e apresentação
   - Reutiliza classes existentes (ConfigManager, PLCCodeGenerator) - princípio DRY
   - APIs RESTful seguem convenções padrão (GET, POST)
   - Tratamento de erros com try/catch e mensagens descritivas
   - Detecção automática de porta disponível (8080-8089)
   - CORS habilitado para desenvolvimento

### Data Flow

1. User connects to SQL Server database via interactive menu
2. Application queries `tblPhaseSteps` and `tblPhaseActivation` tables
3. Data is parsed into `Activation` objects (phase_id, step_no, tag_name, i_type, pid_type)
4. Activations are grouped by step number
5. For each step, generators create activation code with appropriate suffixes
6. Three files written to output directory: `.txt`, `.L5X`, `.scl`

### Configuration System

**Default Type Mapping** (lines 21-27):
- 0: Valve
- 6: Analog Output
- 8: PID
- 10: Communication
- 13: VSD

**Suffix Logic** (lines 29-38, 70-80):
- Most types append `.Activate`
- Communication types have no suffix
- PID types conditional: `.FixedOutput` if `pid_type == 4`, else `.ClosedLoop`

Configuration persists in `plc_config.json` (auto-created on first run).

## Database Schema Requirements

The application expects these SQL Server tables:

**tblPhaseSteps**:
- `iClassID` - Phase identifier
- `iIndexNo` - Step number
- `sName_1` - Step name

**tblPhaseActivation**:
- `iPhaseID` - Links to tblPhaseSteps.iClassID
- `iStepNo` - Links to tblPhaseSteps.iIndexNo
- `iPIDType` - PID type identifier (0 if not PID)
- `iType` - Component type identifier
- `sName_1` - Tag name

## Output Files

Generated in user-specified directory (default: `output/`):

1. **rockwell_ladder.txt** - Human-readable ladder logic with comments
2. **rockwell_ladder.L5X** - XML format for Studio 5000 import (RSLogix5000Content schema)
3. **siemens_scl.scl** - SCL code with REGION blocks for TIA Portal

## Key Implementation Details

- **Step grouping**: Activations are grouped by `step_no` before code generation to ensure logical organization
- **Suffix determination**: Uses two-level lookup (iType → type name → suffix), with special case for PID
- **L5X format**: Simplified XML structure (lines 203-221), may need adjustment for specific Studio 5000 versions
- **Encoding**: All file I/O uses UTF-8 to handle international characters. On Windows, stdout is reconfigured to UTF-8 (PLC_CodeGenerator.py:10-14)
- **Error handling**: Database connection errors print to console but don't crash application
- **Port management**: Web server automatically finds available port if default is in use

## Troubleshooting

### Problemas Comuns

**Erro "ODBC Driver 17 for SQL Server não encontrado":**
- Instalar ODBC Driver 17 for SQL Server da Microsoft
- Download: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

**Erro "ModuleNotFoundError: No module named 'flask'":**
```bash
pip install -r requirements.txt
```

**Porta em uso (Address already in use):**
- O sistema detecta automaticamente uma porta livre entre 8080-8089
- Se persistir, verificar processos usando portas: `netstat -ano | findstr :8080`

**Erro de conexão com banco de dados:**
- Verificar credenciais (servidor, database, username, password)
- Testar conexão manual usando SSMS (SQL Server Management Studio)
- Verificar firewall e permissões de rede
- Para autenticação Windows, deixar username e password vazios

**Arquivos não sendo gerados:**
- Verificar se está conectado ao banco de dados
- Verificar se existem registros nas tabelas tblPhaseSteps e tblPhaseActivation
- Verificar permissões de escrita no diretório de saída

## Exemplos de Uso das APIs

### Conectar ao Banco (Windows Authentication)
```bash
curl -X POST http://localhost:8080/api/database/connect \
  -H "Content-Type: application/json" \
  -d "{\"server\":\"localhost\",\"database\":\"MyDatabase\"}"
```

### Conectar ao Banco (SQL Authentication)
```bash
curl -X POST http://localhost:8080/api/database/connect \
  -H "Content-Type: application/json" \
  -d "{\"server\":\"localhost\",\"database\":\"MyDatabase\",\"username\":\"user\",\"password\":\"pass\"}"
```

### Verificar Status da Conexão
```bash
curl http://localhost:8080/api/database/status
```

### Gerar Códigos PLC
```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"output_dir\":\"output\"}"
```

### Preview de Arquivo Gerado
```bash
curl http://localhost:8080/api/preview/rockwell_ladder.txt?output_dir=output
```

### Download de Arquivo
```bash
curl -O http://localhost:8080/api/download/rockwell_ladder.L5X?output_dir=output
```

### Obter Configurações
```bash
curl http://localhost:8080/api/config
```

### Atualizar Configurações
```bash
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d "{\"type_mapping\":{\"0\":\"Valve\",\"14\":\"NewType\"},\"suffix_mapping\":{\"NewType\":\".CustomSuffix\"}}"
```

## Estrutura de Arquivos do Projeto

```
PLC CodeGenerator/
├── PLC_CodeGenerator.py      # Código principal e CLI
├── app.py                     # Servidor Flask com APIs REST
├── requirements.txt           # Dependências Python
├── plc_config.json           # Configurações de mapeamento (auto-criado)
├── start_server.bat          # Script Windows para iniciar web server
├── start_cli.bat             # Script Windows para iniciar CLI
├── templates/
│   └── index.html            # Interface web HTML/CSS/JavaScript
└── output/                   # Diretório de saída (auto-criado)
    ├── rockwell_ladder.txt   # Código Ladder em texto
    ├── rockwell_ladder.L5X   # Código Ladder em XML
    └── siemens_scl.scl      # Código SCL para Siemens
```
