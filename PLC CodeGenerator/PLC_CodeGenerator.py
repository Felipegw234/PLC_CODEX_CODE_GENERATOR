import pyodbc
import json
import os
import sys
import re
from typing import List
from dataclasses import dataclass
from datetime import datetime

# Configurar encoding para UTF-8 no Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

@dataclass
class Activation:
    """Representa uma ativação de fase"""
    phase_id: int
    step_no: int
    pid_type: int
    i_type: int
    tag_name: str
    step_name: str

    def has_activation(self) -> bool:
        """Verifica se há ativação (tag_name não é None)"""
        return self.tag_name is not None

class ConfigManager:
    """Gerencia configurações de mapeamento"""

    DEFAULT_TYPE_MAPPING = {
        "0": "V",
        "1": "V",
        "2": "V",
        "6": "AO",
        "7": "DO",
        "8": "PID",
        "10": "Comm",
        "13": "VSD",
        "14": "TOT"
    }

    DEFAULT_SUFFIX_MAPPING = {
        "0": ".activate",
        "1": ".activateLL",
        "2": ".activateUL",
        "6": ".activate",
        "7": ".activate",
        "8": {
            "pid_type_4": ".fixedoutput",
            "pid_type_other": ".closeloop"
        },
        "10": "",
        "13": ".activate",
        "14": {
            "pid_type_2": ".ResetTotalizer",
            "pid_type_other": ".EnableTotalizer"
        }
    }

    DEFAULT_PID_TYPE_MAPPING = {
        "0": "N",
        "1": "S",
        "2": "R",
        "3": "SP",
        "4": "FO"
    }

    def __init__(self, config_file: str = "plc_config.json"):
        self.config_file = config_file
        self.type_mapping = self.DEFAULT_TYPE_MAPPING.copy()
        self.suffix_mapping = self.DEFAULT_SUFFIX_MAPPING.copy()
        self.pid_type_mapping = self.DEFAULT_PID_TYPE_MAPPING.copy()
        self.load_config()

    def load_config(self):
        """Carrega configurações do arquivo JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.type_mapping = config.get('type_mapping', self.DEFAULT_TYPE_MAPPING)
                    self.suffix_mapping = config.get('suffix_mapping', self.DEFAULT_SUFFIX_MAPPING)
                    self.pid_type_mapping = config.get('pid_type_mapping', self.DEFAULT_PID_TYPE_MAPPING)
                print(f"✓ Configurações carregadas de {self.config_file}")
            except Exception as e:
                print(f"⚠ Erro ao carregar config: {e}. Usando padrões.")
        else:
            self.save_config()

    def save_config(self):
        """Salva configurações no arquivo JSON"""
        config = {
            'type_mapping': self.type_mapping,
            'suffix_mapping': self.suffix_mapping,
            'pid_type_mapping': self.pid_type_mapping
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"✓ Configurações salvas em {self.config_file}")

    def should_skip_activation(self, i_type: int, pid_type: int) -> bool:
        """
        Determina se uma ativação deve ser desconsiderada baseado nas regras de iPIDType.

        Regras:
        - iPIDType = 3: desconsiderar sempre
        - iPIDType = 4: desconsiderar se iType for (0, 1, 2, 7, 10, 14)
        - iPIDType = 2: desconsiderar, exceto se iType = 14
        """
        # iPIDType = 3: sempre desconsiderar
        if pid_type == 3:
            return True

        # iPIDType = 4: desconsiderar se iType for (0, 1, 2, 7, 10, 14)
        if pid_type == 4 and i_type in [0, 1, 2, 7, 10, 14]:
            return True

        # iPIDType = 2: desconsiderar, exceto se iType = 14
        if pid_type == 2 and i_type != 14:
            return True

        return False

    def get_suffix(self, i_type: int, pid_type: int = None) -> str:
        """Retorna o sufixo adequado baseado no iType e pidType"""
        # Converte i_type para string para lookup no mapeamento
        i_type_str = str(i_type)

        # Verifica se deve pular esta ativação
        if pid_type is not None and self.should_skip_activation(i_type, pid_type):
            return None  # Retorna None para indicar que deve ser ignorada

        # Busca mapeamento de sufixo
        suffix_config = self.suffix_mapping.get(i_type_str, "")

        # Se for um dicionário (casos especiais com pid_type)
        if isinstance(suffix_config, dict):
            if pid_type is not None:
                # iType 8 (PID): verifica pid_type_4
                if i_type == 8:
                    if pid_type == 4:
                        return suffix_config.get("pid_type_4", "")
                    else:
                        return suffix_config.get("pid_type_other", "")
                # iType 14 (TOT): verifica pid_type_2
                elif i_type == 14:
                    if pid_type == 2:
                        return suffix_config.get("pid_type_2", "")
                    else:
                        return suffix_config.get("pid_type_other", "")
            # Se não tem pid_type, retorna o padrão
            return suffix_config.get("pid_type_other", "")

        # Retorna sufixo simples
        return suffix_config

class DatabaseConnection:
    """Gerencia conexão com SQL Server"""
    
    def __init__(self, server: str, database: str, username: str = None, password: str = None):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
    
    def connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            if self.username and self.password:
                conn_str = (
                    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                    f'SERVER={self.server};'
                    f'DATABASE={self.database};'
                    f'UID={self.username};'
                    f'PWD={self.password}'
                )
            else:
                # Autenticação Windows
                conn_str = (
                    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                    f'SERVER={self.server};'
                    f'DATABASE={self.database};'
                    f'Trusted_Connection=yes;'
                )
            
            self.connection = pyodbc.connect(conn_str)
            print(f"✓ Conectado ao banco: {self.database}")
            return True
        except pyodbc.Error as e:
            print(f"✗ Erro de conexão: {e}")
            return False
    
    def disconnect(self):
        """Fecha conexão com o banco"""
        if self.connection:
            self.connection.close()
            print("✓ Conexão fechada")
    
    def fetch_activations(self, phase_instance_id: int = None) -> List[Activation]:
        """Busca ativações do banco de dados com filtro opcional por Phase Instance
        Retorna TODOS os passos, incluindo aqueles sem ativações"""
        if not self.connection:
            raise Exception("Não conectado ao banco de dados")

        # Query base - busca todos os passos, com ou sem ativações
        # Agora usando tblPhaseInstance (iID) ao invés de tblPhaseClass (iClassID)
        query = """
        SELECT
            t3.iID as InstanceID,
            t3.iClassID,
            t2.iIndexNo,
            t2.sName_1 as StepName,
            t1.iPIDType,
            t1.iType,
            t1.sName_1 as TagName
        FROM dbo.tblPhaseInstance t3
        INNER JOIN dbo.tblPhaseSteps t2
            ON t3.iClassID = t2.iClassID
        LEFT JOIN dbo.tblPhaseActivation t1
            ON t3.iID = t1.iPhaseID
            AND t2.iIndexNo = t1.iStepNo
        WHERE 1=1
        """

        # Adiciona filtro de Phase Instance se especificado
        if phase_instance_id is not None:
            query += f" AND t3.iID = {phase_instance_id}"

        query += " ORDER BY t2.iIndexNo, t1.iStepNo"

        cursor = self.connection.cursor()
        cursor.execute(query)

        activations = []
        for row in cursor.fetchall():
            activations.append(Activation(
                phase_id=row.iClassID,
                step_no=row.iIndexNo,
                pid_type=row.iPIDType if row.iPIDType else 0,
                i_type=row.iType if row.iType else 0,
                tag_name=row.TagName,  # Pode ser None para passos sem ativação
                step_name=row.StepName
            ))

        cursor.close()
        filter_msg = f" (filtrado por Phase Instance ID: {phase_instance_id})" if phase_instance_id else ""
        total_activations = sum(1 for act in activations if act.has_activation())
        print(f"✓ {total_activations} ativações encontradas em {len(activations)} registros{filter_msg}")
        return activations

class RockwellGenerator:
    """Gera código Ladder para Rockwell"""

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager

    def _build_rockwell_condition(self, cond_data: dict, step_no: int) -> str:
        """Constrói string de condição para Rockwell com BST/NXB/BND

        Args:
            cond_data: {expression: str, conditions: [{label, tag, negated}]}
            step_no: Número do step
        """
        if not cond_data or not cond_data.get('conditions'):
            return f"XIC StepFlag[{step_no}].Flag"

        expression = cond_data.get('expression', 'X1')
        conditions = cond_data.get('conditions', [])

        # Cria mapa de variáveis
        var_map = {}
        for cond in conditions:
            tag = cond.get('tag', '')
            negated = cond.get('negated', False)
            label = cond.get('label', 'X1')

            instruction = 'XIO' if negated else 'XIC'
            var_map[label] = {'instruction': instruction, 'tag': tag}

        # Se é só X1, retorna simples
        expr = expression.strip()
        if expr == 'X1' and len(conditions) == 1:
            v = var_map.get('X1', {'instruction': 'XIC', 'tag': f'StepFlag[{step_no}].Flag'})
            return f"{v['instruction']} {v['tag']}"

        # Parser de expressões para ladder
        result = []

        # Detecta estrutura principal
        if 'OR' in expr:
            # Tem OR: usar BST/NXB/BND
            parts = expr.split(' OR ')
            result.append('BST')

            for idx, part in enumerate(parts):
                if idx > 0:
                    result.append('NXB')

                # Remove parênteses e processa ANDs
                clean_part = part.replace('(', '').replace(')', '').strip()
                and_parts = clean_part.split(' AND ')

                for var_name in and_parts:
                    v = var_map.get(var_name.strip())
                    if v:
                        result.append(f"{v['instruction']} {v['tag']}")

            result.append('BND')
        else:
            # Só AND: sequencial
            parts = expr.split(' AND ')
            for var_name in parts:
                clean_var = var_name.replace('(', '').replace(')', '').strip()
                v = var_map.get(clean_var)
                if v:
                    result.append(f"{v['instruction']} {v['tag']}")

        return ' '.join(result)

    def generate_text(self, activations: List[Activation], activation_conditions: dict = None) -> str:
        """Gera código Ladder em formato texto

        Args:
            activations: Lista de ativações
            activation_conditions: Dicionário de condicionais por ativação
                {step_no: {tag_with_suffix: {operator: str, conditions: list}}}
        """
        code_lines = []
        code_lines.append("="*80)
        code_lines.append("Código Ladder Gerado Automaticamente")
        code_lines.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        code_lines.append("="*80)
        code_lines.append("")

        # Agrupa por step
        steps = {}
        for act in activations:
            if act.step_no not in steps:
                steps[act.step_no] = {'name': act.step_name, 'activations': []}
            # Adiciona apenas ativações válidas (com tag_name)
            if act.has_activation():
                steps[act.step_no]['activations'].append(act)

        # Gera código para cada step
        for step_no in sorted(steps.keys()):
            step_data = steps[step_no]
            code_lines.append(f"{'-'*80}")
            code_lines.append(f"Step {step_no:02d} -- {step_data['name']}")
            code_lines.append(f"{'-'*80}")

            # Gera linhas de ativação se houver
            for act in step_data['activations']:
                suffix = self.config.get_suffix(act.i_type, act.pid_type)

                # Pula ativação se deve ser desconsiderada (get_suffix retorna None)
                if suffix is None:
                    continue

                tag_with_suffix = f"{act.tag_name}{suffix}"

                # Verifica se há condicionais customizadas
                if (activation_conditions and
                    step_no in activation_conditions and
                    tag_with_suffix in activation_conditions[step_no]):

                    cond_data = activation_conditions[step_no][tag_with_suffix]
                    condition_str = self._build_rockwell_condition(cond_data, step_no)
                else:
                    # Condição padrão: StepFlag
                    condition_str = f"XIC StepFlag[{step_no}].Flag"

                code_lines.append(f"{condition_str} OTL {tag_with_suffix}")

            code_lines.append("")

        return "\n".join(code_lines)
    
    def generate_l5x(self, activations: List[Activation], activation_conditions: dict = None, routine_name: str = "CM_Valve", program_name: str = "Phase01001_SEQ_DF_Master") -> str:
        """Gera código em formato .L5X completo seguindo padrão GEA

        Args:
            activations: Lista de ativações
            activation_conditions: Dicionário de condicionais por ativação
            routine_name: Nome da rotina (default: CM_Valve)
            program_name: Nome do programa (default: Phase01001_SEQ_DF_Master)
        """
        from datetime import datetime

        # Agrupa por step
        steps = {}
        for act in activations:
            if act.step_no not in steps:
                steps[act.step_no] = {'name': act.step_name, 'activations': []}
            # Adiciona apenas ativações válidas (com tag_name)
            if act.has_activation():
                steps[act.step_no]['activations'].append(act)

        # Conta total de rungs (steps + ativações)
        total_rungs = 0
        for step_no in sorted(steps.keys()):
            total_rungs += 1  # Rung do comentário do step
            step_data = steps[step_no]
            for act in step_data['activations']:
                suffix = self.config.get_suffix(act.i_type, act.pid_type)
                if suffix is not None:
                    total_rungs += 1

        # Data de exportação
        export_date = datetime.now().strftime("%a %b %d %H:%M:%S %Y")

        # Header com atributos completos
        l5x_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="37.00" TargetType="Rung" TargetCount="{total_rungs}" CurrentLanguage="en-US" ContainsContext="true" ExportDate="{export_date}" ExportOptions="References NoRawData L5KData DecoratedData Context RoutineLabels AliasExtras IOTags NoStringData ForceProtectedEncoding AllProjDocTrans">
<Controller Use="Context" Name="_GEA_Codex">
<DataTypes Use="Context">
<DataType Name="PhaseControl_StepFlags" Family="NoFamily" Class="User">
<Description>
<LocalizedDescription Lang="en-US">
<![CDATA[Step Flags for Each Step -]]>
</LocalizedDescription>
</Description>
<Members>
<Member Name="ZZZZZZZZZZPhaseContr0" DataType="SINT" Dimension="0" Radix="Decimal" Hidden="true" ExternalAccess="Read/Write"/>
<Member Name="Flag" DataType="BIT" Dimension="0" Radix="Decimal" Hidden="false" Target="ZZZZZZZZZZPhaseContr0" BitNumber="0" ExternalAccess="Read/Write">
<Description>
<LocalizedDescription Lang="en-US">
<![CDATA[- Equal to]]>
</LocalizedDescription>
</Description>
</Member>
<Member Name="FlagLE" DataType="BIT" Dimension="0" Radix="Decimal" Hidden="false" Target="ZZZZZZZZZZPhaseContr0" BitNumber="1" ExternalAccess="Read/Write">
<Description>
<LocalizedDescription Lang="en-US">
<![CDATA[- Less than or Equal to]]>
</LocalizedDescription>
</Description>
</Member>
<Member Name="FlagGE" DataType="BIT" Dimension="0" Radix="Decimal" Hidden="false" Target="ZZZZZZZZZZPhaseContr0" BitNumber="2" ExternalAccess="Read/Write">
<Description>
<LocalizedDescription Lang="en-US">
<![CDATA[- Greater than or Equal to]]>
</LocalizedDescription>
</Description>
</Member>
</Members>
</DataType>
</DataTypes>
<Programs Use="Context">
<Program Use="Context" Name="{program_name}">
<Tags Use="Context">
<Tag Name="StepFlag" TagType="Base" DataType="PhaseControl_StepFlags" Dimensions="128" Constant="false" ExternalAccess="Read/Write" OpcUaAccess="None">
<Comments>
"""

        # Adiciona comentários para os steps
        for step_no in sorted(steps.keys()):
            step_data = steps[step_no]
            l5x_content += f"""<Comment Operand="[{step_no}]">
<LocalizedComment Lang="en-US">
<![CDATA[{step_data['name']}]]>
</LocalizedComment>
</Comment>
"""

        # Data em formato L5K (128 elementos)
        l5x_data_values = ['[2]'] * 128
        l5x_data_values[0] = '[7]'  # Step 0 inicializado
        l5x_content += f"""</Comments>
<Data Format="L5K">
<![CDATA[[{','.join(l5x_data_values)}]]]>
</Data>
<Data Format="Decorated">
<Array DataType="PhaseControl_StepFlags" Dimensions="128">
"""

        # Data em formato Decorated (128 elementos)
        for i in range(128):
            flag_val = "1" if i == 0 else "0"
            flagle_val = "1"
            flagge_val = "1" if i == 0 else "0"
            l5x_content += f"""<Element Index="[{i}]">
<Structure DataType="PhaseControl_StepFlags">
<DataValueMember Name="Flag" DataType="BOOL" Value="{flag_val}"/>
<DataValueMember Name="FlagLE" DataType="BOOL" Value="{flagle_val}"/>
<DataValueMember Name="FlagGE" DataType="BOOL" Value="{flagge_val}"/>
</Structure>
</Element>
"""

        l5x_content += """</Array>
</Data>
</Tag>
</Tags>
<Routines Use="Context">
<Routine Use="Context" Name="{routine_name}">
<RLLContent Use="Context">
""".replace("{routine_name}", routine_name)

        # Gera rungs
        rung_number = 2  # Começa em 2 como no exemplo

        for step_no in sorted(steps.keys()):
            step_data = steps[step_no]

            # Rung de comentário do step
            separator = "-" * 80
            l5x_content += f"""<Rung Use="Target" Number="{rung_number}" Type="N">
<Comment>
<LocalizedComment Lang="en-US">
<![CDATA[{separator}
Step {step_no:02d} -- {step_data['name']}
{separator}]]>
</LocalizedComment>
</Comment>
<Text>
<![CDATA[NOP();]]>
</Text>
</Rung>
"""
            rung_number += 1

            # Gera rungs de ativações
            for act in step_data['activations']:
                suffix = self.config.get_suffix(act.i_type, act.pid_type)

                # Pula ativação se deve ser desconsiderada
                if suffix is None:
                    continue

                tag_with_suffix = f"{act.tag_name}{suffix}"

                # Verifica se há condicionais customizadas
                if (activation_conditions and
                    step_no in activation_conditions and
                    tag_with_suffix in activation_conditions[step_no]):

                    cond_data = activation_conditions[step_no][tag_with_suffix]
                    condition_str = self._build_rockwell_condition(cond_data, step_no)

                    # Converte para formato L5X (com parênteses nas tags)
                    # Adiciona parênteses nas instruções XIC/XIO
                    ladder_condition = re.sub(r'(XIC|XIO)\s+([A-Za-z0-9_\[\]\.]+)', r'\1(\2)', condition_str)

                    # Converte BST/NXB/BND para formato L5X com colchetes
                    # BST -> [
                    # NXB -> ,
                    # BND -> ]
                    ladder_condition = ladder_condition.replace('BST ', '[')
                    ladder_condition = ladder_condition.replace(' NXB ', ' ,')
                    ladder_condition = ladder_condition.replace(' BND', ' ]')
                else:
                    # Condição padrão: StepFlag
                    ladder_condition = f"XIC(StepFlag[{step_no}].Flag)"

                l5x_content += f"""<Rung Use="Target" Number="{rung_number}" Type="N">
<Text>
<![CDATA[{ladder_condition}OTL({tag_with_suffix});]]>
</Text>
</Rung>
"""
                rung_number += 1

        # Footer
        l5x_content += """</RLLContent>
</Routine>
</Routines>
</Program>
</Programs>
</Controller>
</RSLogix5000Content>
"""

        return l5x_content

class SiemensGenerator:
    """Gera código SCL para Siemens"""

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager

    def _convert_stepflag_to_siemens(self, tag: str) -> str:
        """Converte StepFlag[N].Flag para #MyStepFlag.StepNNN"""
        import re
        match = re.match(r'StepFlag\[(\d+)\]\.Flag', tag, re.IGNORECASE)
        if match:
            step_num = int(match.group(1))
            return f"#MyStepFlag.Step{step_num:03d}"
        return tag

    def _build_siemens_condition(self, cond_data: dict, step_no: int) -> str:
        """Constrói string de condição para Siemens baseado na expressão lógica

        Args:
            cond_data: {expression: str, conditions: [{label, tag, negated}]}
            step_no: Número do step
        """
        if not cond_data or not cond_data.get('conditions'):
            return f"#MyStepFlag.Step{step_no:03d}"

        expression = cond_data.get('expression', 'X1')
        conditions = cond_data.get('conditions', [])

        # Cria mapa de variáveis
        var_map = {}
        for cond in conditions:
            tag = cond.get('tag', '')
            negated = cond.get('negated', False)
            label = cond.get('label', 'X1')

            # Converte StepFlag automaticamente
            tag = self._convert_stepflag_to_siemens(tag)

            # Siemens: NOT para negação
            var_map[label] = f"NOT {tag}" if negated else tag

        # Substitui variáveis na expressão
        result = expression

        # Ordena do maior para o menor (X10 antes de X1)
        labels = sorted(var_map.keys(), key=lambda x: int(x[1:]), reverse=True)

        for label in labels:
            result = result.replace(label, var_map[label])

        return result

    def generate_scl(self, activations: List[Activation], activation_conditions: dict = None) -> str:
        """Gera código SCL

        Args:
            activations: Lista de ativações
            activation_conditions: Dicionário de condicionais por ativação
                {step_no: {tag_with_suffix: {operator: str, conditions: list}}}
        """
        code_lines = []
        code_lines.append("(* " + "="*80 + " *)")
        code_lines.append("(* Código SCL Gerado Automaticamente *)")
        code_lines.append(f"(* Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} *)")
        code_lines.append("(* " + "="*80 + " *)")
        code_lines.append("")

        # Agrupa por step
        steps = {}
        for act in activations:
            if act.step_no not in steps:
                steps[act.step_no] = {'name': act.step_name, 'activations': []}
            # Adiciona apenas ativações válidas (com tag_name)
            if act.has_activation():
                steps[act.step_no]['activations'].append(act)

        # Gera código para cada step
        for step_no in sorted(steps.keys()):
            step_data = steps[step_no]
            code_lines.append(f"REGION Step {step_no:02d} - {step_data['name']}")

            if step_data['activations']:
                # MyStepFlag no IF principal
                step_flag = f"#MyStepFlag.Step{step_no:03d}"
                code_lines.append(f"    IF {step_flag} THEN")

                # Todas as ativações dentro do mesmo IF
                for act in step_data['activations']:
                    suffix = self.config.get_suffix(act.i_type, act.pid_type)

                    # Pula ativação se deve ser desconsiderada (get_suffix retorna None)
                    if suffix is None:
                        continue

                    # Chave sem aspas para buscar nas condições
                    tag_with_suffix_key = f"{act.tag_name}{suffix}"
                    # Tag com aspas para o código SCL
                    tag_with_suffix_scl = f'"{act.tag_name}"{suffix}'

                    # Verifica se há condicionais customizadas para esta ativação
                    cond_expr = 'TRUE'  # Padrão
                    if (activation_conditions and
                        step_no in activation_conditions and
                        tag_with_suffix_key in activation_conditions[step_no]):

                        cond_data = activation_conditions[step_no][tag_with_suffix_key]
                        # Se tem expressão diferente de X1, usa ela
                        if cond_data.get('expression', 'X1') != 'X1':
                            cond_expr = self._build_siemens_condition(cond_data, step_no)

                    code_lines.append(f"        {tag_with_suffix_scl} := {cond_expr};")

                code_lines.append("        RETURN;")
                code_lines.append("    END_IF;")
            else:
                # Sem ativações: IF com RETURN vazio
                step_flag = f"#MyStepFlag.Step{step_no:03d}"
                code_lines.append(f"    IF {step_flag} THEN")
                code_lines.append("        RETURN;")
                code_lines.append("    END_IF;")

            code_lines.append("END_REGION ;")
            code_lines.append("")

        return "\n".join(code_lines)

class PLCCodeGenerator:
    """Classe principal do gerador"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.db = None
        self.rockwell_gen = RockwellGenerator(self.config)
        self.siemens_gen = SiemensGenerator(self.config)
    
    def connect_database(self, server: str, database: str, username: str = None, password: str = None):
        """Conecta ao banco de dados"""
        self.db = DatabaseConnection(server, database, username, password)
        return self.db.connect()
    
    def generate_all(self, output_dir: str = "output"):
        """Gera todos os códigos"""
        if not self.db or not self.db.connection:
            print("✗ Não conectado ao banco de dados")
            return
        
        # Cria diretório de saída
        os.makedirs(output_dir, exist_ok=True)
        
        # Busca ativações
        print("\n📊 Buscando dados do banco...")
        activations = self.db.fetch_activations()
        
        if not activations:
            print("⚠ Nenhuma ativação encontrada")
            return
        
        # Gera código Rockwell (texto)
        print("\n🔧 Gerando código Ladder (Rockwell - Texto)...")
        ladder_text = self.rockwell_gen.generate_text(activations)
        ladder_file = os.path.join(output_dir, "rockwell_ladder.txt")
        with open(ladder_file, 'w', encoding='utf-8') as f:
            f.write(ladder_text)
        print(f"✓ Salvo em: {ladder_file}")
        
        # Gera código Rockwell (.L5X)
        print("\n🔧 Gerando código Ladder (Rockwell - L5X)...")
        l5x_code = self.rockwell_gen.generate_l5x(activations)
        l5x_file = os.path.join(output_dir, "rockwell_ladder.L5X")
        with open(l5x_file, 'w', encoding='utf-8') as f:
            f.write(l5x_code)
        print(f"✓ Salvo em: {l5x_file}")
        
        # Gera código Siemens (SCL)
        print("\n🔧 Gerando código SCL (Siemens)...")
        scl_code = self.siemens_gen.generate_scl(activations)
        scl_file = os.path.join(output_dir, "siemens_scl.scl")
        with open(scl_file, 'w', encoding='utf-8') as f:
            f.write(scl_code)
        print(f"✓ Salvo em: {scl_file}")
        
        print("\n✅ Geração concluída com sucesso!")
        print(f"📁 Arquivos salvos em: {os.path.abspath(output_dir)}")
    
    def edit_config(self):
        """Abre editor de configurações interativo"""
        print("\n" + "="*60)
        print("EDITOR DE CONFIGURAÇÕES")
        print("="*60)
        
        while True:
            print("\n1. Ver mapeamento de tipos (iType)")
            print("2. Ver mapeamento de sufixos")
            print("3. Adicionar/Editar tipo")
            print("4. Adicionar/Editar sufixo")
            print("5. Salvar configurações")
            print("6. Voltar")
            
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == "1":
                print("\n📋 Mapeamento de Tipos:")
                for key, value in sorted(self.config.type_mapping.items()):
                    print(f"  {key}: {value}")
            
            elif choice == "2":
                print("\n📋 Mapeamento de Sufixos:")
                for key, value in self.config.suffix_mapping.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for k, v in value.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"  {key}: {value}")
            
            elif choice == "3":
                i_type = input("Digite o iType (número): ").strip()
                type_name = input("Digite o nome do tipo: ").strip()
                try:
                    self.config.type_mapping[int(i_type)] = type_name
                    print(f"✓ Tipo {i_type} → {type_name} adicionado")
                except ValueError:
                    print("✗ iType deve ser um número")
            
            elif choice == "4":
                type_name = input("Digite o nome do tipo: ").strip()
                suffix = input("Digite o sufixo (ex: .Activate): ").strip()
                self.config.suffix_mapping[type_name] = suffix
                print(f"✓ Sufixo para {type_name} → {suffix} adicionado")
            
            elif choice == "5":
                self.config.save_config()
            
            elif choice == "6":
                break

def main():
    """Função principal com menu interativo"""
    generator = PLCCodeGenerator()
    
    print("="*60)
    print("  GERADOR DE CÓDIGO LADDER E SCL")
    print("  Rockwell Studio 5000 | Siemens TIA Portal")
    print("="*60)
    
    while True:
        print("\n📋 MENU PRINCIPAL")
        print("1. Conectar ao banco de dados")
        print("2. Gerar códigos")
        print("3. Editar configurações")
        print("4. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            print("\n🔌 CONEXÃO COM SQL SERVER")
            server = input("Servidor (ex: localhost ou IP): ").strip()
            database = input("Nome do banco de dados: ").strip()
            
            use_auth = input("Usar autenticação SQL? (s/n): ").strip().lower()
            
            if use_auth == 's':
                username = input("Usuário: ").strip()
                password = input("Senha: ").strip()
                generator.connect_database(server, database, username, password)
            else:
                generator.connect_database(server, database)
        
        elif choice == "2":
            if not generator.db:
                print("\n⚠ Conecte ao banco de dados primeiro!")
            else:
                output_dir = input("\nDiretório de saída (Enter para 'output'): ").strip()
                if not output_dir:
                    output_dir = "output"
                generator.generate_all(output_dir)
        
        elif choice == "3":
            generator.edit_config()
        
        elif choice == "4":
            if generator.db:
                generator.db.disconnect()
            print("\n👋 Até logo!")
            break
        
        else:
            print("\n✗ Opção inválida")

if __name__ == "__main__":
    main()